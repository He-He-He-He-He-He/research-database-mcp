"""Pip retries use existing settings; optional explicit mirror, TLS always checked."""
import re,subprocess
from urllib.parse import urlsplit

def validate_index(url):
    if url is None:return None
    p=urlsplit(url)
    if p.scheme!='https' or not p.hostname or p.username or p.password or p.query or p.fragment:raise ValueError('软件源须为不含账号、密码或查询参数的HTTPS地址；不关闭证书校验')
    return url

def dependencies(python,requirements,index_url=None,fallback_index_url=None):
    index_url=validate_index(index_url);fallback_index_url=validate_index(fallback_index_url)
    attempted=[]
    for index in [index_url]+([fallback_index_url] if fallback_index_url and fallback_index_url!=index_url else []):
        args=[str(python),'-m','pip','install','--timeout','15','--retries','2','-r',str(requirements)]
        if index:args+=['--index-url',index]
        attempted.append(index or 'existing-pip-settings')
        try:
            p=subprocess.run(args,capture_output=True,text=True,timeout=180)
            if p.returncode==0:return {'installed':True,'attempted_sources':attempted}
            error=(p.stderr or '')+'\n'+(p.stdout or '')
            network=bool(re.search(r'Timeout|timed out|NewConnectionError|NameResolutionError|Temporary failure in name resolution|Network is unreachable|Connection reset|ProxyError',error,re.I))
            if re.search(r'CERTIFICATE_VERIFY_FAILED|SSLError',error,re.I):raise RuntimeError('依赖安装遇到证书校验错误；未关闭TLS校验，请检查当前代理和CA设置')
            if not network:raise RuntimeError('依赖安装失败（不属于已确认网络故障）；原有环境和进度保留，请核对Python版本及依赖兼容性')
        except subprocess.TimeoutExpired:pass
        if index==fallback_index_url or not fallback_index_url:break
    raise RuntimeError('依赖下载连接失败；保留已有设置，可重试或用 --fallback-index-url 显式指定可信HTTPS镜像。未打印私有软件源或凭据')
