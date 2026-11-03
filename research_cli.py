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

ROOT = Path(__file__).resolve().parent

def catalog():
    return json.loads((ROOT/'command_catalog.json').read_text(encoding='utf-8'))['commands']

def scrub(text):
    # Redact explicitly supplied credentials before returning upstream errors.
    for k,v in os.environ.items():
        if k.startswith('RESEARCH_MCP_') and re.search('KEY|TOKEN|SECRET|PASSWORD|COOKIE',k) and len(v)>5:
            text=text.replace(v,'[REDACTED]')
    text=re.sub(r'(?i)([?&](?:api[_-]?key|access_token|token|key|subscription-key)=)[^&\s"<>]+',r'\1[REDACTED]',text)
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
        return {'ok':False,'error':'choose_mode','message':'请先用 research_setup 选择 partial 或 full。'}
    if not help_only and state['mode']=='partial' and not entry.get('starter'):
        return {'ok':False,'error':'optional_setup_required','message':'这个命令属于扩展功能；切换full可逐项配置，免登录功能仍可使用。','requirements':entry}
    if help_only:args=['--help']
    # A small orphaned official adapter is exposed through a proper CLI bridge.
    target='cas_bridge.py' if command.startswith('cas-common-') else 'engine/research.py'
    environment=rt.subprocess_environment()
    environment['PYTHONDONTWRITEBYTECODE']='1'
    environment['RESEARCH_MCP_ENGINE']='1'
    environment['PYTHONPATH']=str(ROOT)+os.pathsep+str(ROOT/'engine')
    try:
        p=subprocess.run([sys.executable,str(ROOT/target),command,*args],cwd=ROOT,env=environment,capture_output=True,text=True,timeout=min(120,max(5,int(timeout))))
    except subprocess.TimeoutExpired:
        return {'ok':False,'error':'upstream_timeout','message':'上游超时；保留配置进度，可以先用其他来源。','command':command}
    stdout,stderr=scrub(p.stdout),scrub(p.stderr)
    if p.returncode:
        category='upstream_or_configuration_error'
        if 'ModuleNotFoundError' in stderr:category='missing_dependency'
        if 'FileNotFoundError' in stderr:category='missing_public_resource'
        return {'ok':False,'command':command,'error':category,'message':stderr[-3000:] or stdout[-3000:],'hint':'查阅命令帮助与需求标记；需要公开文件时请自行获取，不能把缺文件解释为无数据。'}
    if help_only:return {'ok':True,'command':command,'help':stdout[:30000],'requirements':entry}
    if len(stdout)>1500000:return {'ok':False,'error':'response_too_large','message':'返回过大，请减少数量、时间范围或分页。'}
    try:value=json.loads(stdout)
    except json.JSONDecodeError:
        return {'ok':False,'command':command,'error':'unexpected_output','message':'没有取得可验证的JSON结果；可能是帮助、页面变化或登录拦截。','preview':stdout[:1500]}
    failure=isinstance(value,dict) and (value.get('ok') is False or value.get('success') is False or bool(value.get('error')) or value.get('status') in ('error','blocked','unavailable'))
    return {'ok':not failure,'command':command,'result':value,'requirements':entry,'source':'research-mcp','verification':'真实命令返回；不代表机构授权、完整覆盖或其他参数已通过。'}

def main():
    parser=argparse.ArgumentParser(description='Research MCP release CLI')
    parser.add_argument('command');parser.add_argument('args',nargs=argparse.REMAINDER)
    a=parser.parse_args()
    try:result=query(a.command,a.args,help_only=a.args==['--help'])
    except (ValueError,TypeError) as exc:result={'ok':False,'error':str(exc)}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result.get('ok') else 1
if __name__=='__main__':sys.exit(main())
