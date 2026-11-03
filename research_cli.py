"""Safe argument-vector entrypoint for the distributable research engine."""
import sys
sys.dont_write_bytecode=True
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
import release_runtime as rt
import access_policy as policy
import network_health

ROOT = Path(__file__).resolve().parent

def catalog():
    return json.loads((ROOT/'command_catalog.json').read_text(encoding='utf-8'))['commands']

def scrub(text):
    # Redact explicitly supplied credentials before returning upstream errors.
    for k,v in os.environ.items():
        if k.startswith('RESEARCH_MCP_') and re.search('KEY|TOKEN|SECRET|PASSWORD|COOKIE',k) and len(v)>5:
            text=text.replace(v,'[REDACTED]')
    text=re.sub(r'(?i)([?&](?:api[_-]?key|access_token|token|key|subscription-key|sig|signature|x-amz-signature|x-amz-security-token|x-amz-credential)=)[^&\s"<>]+',r'\1[REDACTED]',text)
    text=re.sub(r'(?i)(Authorization\s*[:=]\s*)(?:Bearer\s+)?[^\s"<>]+',r'\1[REDACTED]',text)
    return text

def query(command,args=None,timeout=90,help_only=False):
    args=[] if args is None else args
    if not isinstance(command,str) or not isinstance(args,list) or len(args)>40 or any(not isinstance(a,str) or len(a)>4000 or '\x00' in a for a in args):
        raise ValueError('命令和参数格式无效；args应为字符串数组')
    entry=next((x for x in catalog() if x['command']==command),None)
    if not entry:raise ValueError('目录中没有这个命令，请先发现来源')
    if any(re.match(r'^--?(?:api[-_]?key|token|password|cookie|authorization|secret)(?:=|$)',a,re.I) for a in args):
        raise ValueError('请使用本机安全存储，不要在MCP参数中传递密钥')
    state=rt.load_state()
    if not help_only and state['mode'] is None:
        return {'ok':False,'error':'choose_mode','message':'请先用 research_setup 选择 general、zju 或 login；一般模式已开放全部无需个人凭据及机构网络的命令。'}
    if not help_only and not policy.allowed(state['mode'],entry):
        required=policy.required(entry)
        return {'ok':False,'command':command,'error':'mode_required','required_mode':required,'message':'此命令需要'+policy.LABELS[required]+'。','hint':'仅切换对应模式，不需重新安装；机构模式仍需真实网络身份，登录模式按需配置自己的账号或 API 凭据。公开功能不受影响。','requirements':entry}
    if help_only:args=['--help']
    # A small orphaned official adapter is exposed through a proper CLI bridge.
    target='cas_bridge.py' if command.startswith('cas-common-') else 'engine/research.py'
    environment=rt.subprocess_environment()
    environment['PYTHONDONTWRITEBYTECODE']='1'
    environment['RESEARCH_MCP_ENGINE']='1'
    environment['PYTHONPATH']=str(ROOT)+os.pathsep+str(ROOT/'engine')
    environment.pop('RESEARCH_MCP_VALIDATE_ONLY',None)
    if not help_only:
        # Validate syntax before applying a cached network skip. A prior timeout
        # must never hide a caller's new --rows/--size mistake.
        validenv={**environment,'RESEARCH_MCP_VALIDATE_ONLY':'1'}
        try:
            validation=subprocess.run([sys.executable,str(ROOT/target),command,*args],cwd=ROOT,env=validenv,capture_output=True,text=True,encoding='utf-8',timeout=15)
        except subprocess.TimeoutExpired:
            return {'ok':False,'error':'local_validation_timeout','command':command,'message':'本地参数校验超时，未把它认定为外网不可达。'}
        if validation.returncode==0:
            previous=network_health.blocked(entry)
            if previous:return network_health.skip_result(entry,previous)
        else:
            # Reuse the normal diagnostic path without launching another process.
            p=validation
    try:
        if help_only or validation.returncode==0:
            p=subprocess.run([sys.executable,str(ROOT/target),command,*args],cwd=ROOT,env=environment,capture_output=True,text=True,encoding='utf-8',timeout=min(120,max(5,int(timeout))))
    except subprocess.TimeoutExpired:
        return network_health.record(entry,{'ok':False,'error':'upstream_timeout','message':'上游超时；保留配置进度，可以先用其他来源。','command':command})
    stdout,stderr=scrub(p.stdout),scrub(p.stderr)
    if p.returncode:
        from diagnostics import environment_summary
        category='upstream_or_configuration_error';details={};message=stderr[-3000:] or stdout[-3000:]
        try:
            body=json.loads(stderr.strip() or stdout.strip())
            if isinstance(body,dict):
                message=str(body.get('error',message));details=body.get('diagnostics') or {}
        except (ValueError,TypeError):pass
        kind=details.get('kind')
        if kind=='invalid_arguments' or p.returncode==2:
            if kind!='invalid_arguments':
                matches=re.findall(r'(?:^|\n)[^\n]*?: error: ([^\n]+)',stderr)
                if matches:message=matches[-1]
            hint='调用 research_help(command='+json.dumps(command,ensure_ascii=False)+') 查看本命令参数；不同来源的数量参数并不相同。'
            if entry.get('count_option'):hint+=' 本命令使用 '+entry['count_option']+'。'
            return {'ok':False,'command':command,'error':'invalid_arguments','message':message[:1000],'usage':details.get('usage',entry.get('usage','')),'supported_options':details.get('supported_options',[]),'hint':hint,'example_args':entry.get('example_args'),'diagnostics':{'kind':'invalid_arguments'}}
        mapping={'http_status':'upstream_http_error','tls_error':'network_tls_error','tls_configuration_error':'network_tls_error','proxy_error':'network_proxy_error','dns_error':'network_dns_error','connection_error':'network_connection_error','network_timeout':'upstream_timeout','transport_unavailable':'missing_transport','invalid_json_response':'upstream_response_error','invalid_response':'upstream_response_error','redirect_error':'upstream_redirect_error','response_too_large':'response_too_large'}
        if entry.get('credential') and re.search(r'需要.*(?:密钥|凭据|API_KEY)|(?:未配置|无法读取|缺少).*(?:密钥|凭据)|(?:密钥|凭据).*(?:未配置|未找到|不存在)|(?:missing|required|not configured).*(?:api.?key|credential)',message,re.I):category='credential_required'
        elif kind in mapping:category=mapping[kind]
        elif 'ModuleNotFoundError' in stderr or details.get('exception_type')=='ModuleNotFoundError':category='missing_dependency'
        elif 'FileNotFoundError' in stderr or details.get('exception_type')=='FileNotFoundError':category='missing_public_resource'
        elif details.get('exception_type')=='ValueError':category='invalid_arguments_or_response'
        hints={'credential_required':'此来源需要接收者自己的账号或 API 凭据；按 research_setup 的指定来源引导配置，不能以机构 IP 替代 API 密钥。先使用其他已可用来源。','invalid_arguments_or_response':'先核对参数取值和返回格式；旧适配器的 ValueError 仍可能来自输入或响应校验，不应直接判为网络或凭据问题。','missing_dependency':'此命令缺少依赖库；按缺失库安装，必要时使用 --extras。','missing_public_resource':'此命令需要公开文件；请根据帮助提供文件。缺文件不代表无数据。','upstream_http_error':'检查具体接口返回的 HTTP 状态、来源访问条件和限流提示。','network_tls_error':'检查运行环境的证书链和 CA 设置；不要关闭证书校验。','network_proxy_error':'检查当前进程的代理配置，不要公开代理凭据。','network_dns_error':'检查运行环境是否能解析具体接口域名。','upstream_timeout':'缩小查询或稍后再试；先保留配置并使用其他来源。'}
        return network_health.record(entry,{'ok':False,'command':command,'error':category,'message':message,'diagnostics':{**details,'environment':environment_summary()},'hint':hints.get(category,'查看具体错误类型和该命令帮助；首页返回200不能证明同一查询可用。')})
    if help_only:return {'ok':True,'command':command,'help':stdout[:30000],'requirements':entry}
    if len(stdout)>1500000:return {'ok':False,'error':'response_too_large','message':'返回过大，请减少数量、时间范围或分页。'}
    try:value=json.loads(stdout)
    except json.JSONDecodeError:
        return {'ok':False,'command':command,'error':'unexpected_output','message':'没有取得可验证的JSON结果；可能是帮助、页面变化或登录拦截。','preview':stdout[:1500]}
    failure=isinstance(value,dict) and (value.get('ok') is False or value.get('success') is False or bool(value.get('error')) or value.get('status') in ('error','blocked','unavailable'))
    partial=isinstance(value,dict) and bool(value.get('failed_pages'))
    if partial and value.get('pages',value.get('scanned',0))==0:failure=True
    result={'ok':not failure,'command':command,'result':value,'requirements':entry,'source':'research-mcp','partial':partial,'result_kind':entry.get('result_kind','unclassified'),'verification':'真实命令返回；目录、元数据与数值不同，单次成功不代表完整覆盖、机构授权或其他参数通过。'}
    if command in ('nbs-annual-series','nbs-frequency-series') and isinstance(value,dict):
        import math
        values=[point.get('value') for period in value.get('data',[]) for point in period.get('values',[])]
        def numeric(item):
            try:return item is not None and math.isfinite(float(str(item).replace(',','')))
            except (TypeError,ValueError):return False
        result['numeric_observation_count']=sum(numeric(item) for item in values)
        if result['numeric_observation_count']==0:result['warnings']=['源返回了响应，但本次没有数值观测；不能把时期行当作数值，也不能将缺失值补成零。']
    if partial:
        result.setdefault('warnings',[]).append('部分请求失败，结果不完整；请查看result.failed_pages。')
        if failure:result['error']='upstream_scan_failed'
    return result

def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description='Research MCP release CLI')
    parser.add_argument('command');parser.add_argument('args',nargs=argparse.REMAINDER)
    a=parser.parse_args()
    try:result=query(a.command,a.args,help_only=a.args==['--help'])
    except (ValueError,TypeError) as exc:result={'ok':False,'error':str(exc)}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result.get('ok') else 1
if __name__=='__main__':sys.exit(main())
