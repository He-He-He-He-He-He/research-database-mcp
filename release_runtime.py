"""Isolated state and credential bridge. No legacy account stores are queried."""
import getpass, json, os, re, subprocess, sys, tempfile
from pathlib import Path
from collections.abc import Mapping

_seen_credentials=set()
_last_transport_error=None

def transport_error():
    """Actual last curl failure in this process, without a URL query or headers."""
    return dict(_last_transport_error) if _last_transport_error else None

def subprocess_environment():
    allowed={'PATH','SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','TEMP','TMP','TMPDIR','LANG','LC_ALL','LC_CTYPE','APPDATA','LOCALAPPDATA','USERPROFILE','HTTPS_PROXY','HTTP_PROXY','ALL_PROXY','NO_PROXY','https_proxy','http_proxy','all_proxy','no_proxy','SSL_CERT_FILE','SSL_CERT_DIR','REQUESTS_CA_BUNDLE','CURL_CA_BUNDLE'}
    env={k:v for k,v in os.environ.items() if k in allowed or k.startswith('RESEARCH_MCP_')}
    root=Path(__file__).resolve().parent
    env['PYTHONPATH']=str(root)+os.pathsep+str(root/'engine')
    env['PYTHONDONTWRITEBYTECODE']='1'
    env['PYTHONUTF8']='1'
    env['PYTHONIOENCODING']='utf-8'
    env['NETRC']=str(state_root()/'no-user-netrc')
    return env

SERVICES={
 'research-toolkit-eia':'eia','research-toolkit-cinii':'cinii','research-toolkit-aseanstats':'asean',
 'research-toolkit-undp-dataprism':'undp','research-toolkit-wto-standard':'wto',
 'research-toolkit-springer-meta':'springer','research-toolkit-wos-starter':'wos',
 'research-toolkit.iom-dtm':'iom-baseline','research-toolkit.iom-hna':'iom-hna',
 'research-toolkit-iati-exploratory':'iati','zju-research-un-population-api':'un-population'}

def state_root():
    override=os.environ.get('RESEARCH_MCP_STATE_DIR')
    if override:return Path(override).expanduser().resolve()
    base=Path(os.environ.get('APPDATA',str(Path.home()/'.config'))) if sys.platform=='win32' else Path.home()/'.config'
    return base/'research-mcp-publisher'

def load_state():
    p=state_root()/'progress.json'
    if not p.exists():return {'schema':2,'mode':None,'progress':{}}
    d=json.loads(p.read_text(encoding='utf-8'))
    from access_policy import normalize
    if d.get('schema') not in (1,2) or not isinstance(d.get('progress'),dict):raise ValueError('配置进度格式异常，请保留文件后检查')
    d['mode']=normalize(d.get('mode'));d['schema']=2
    return d

def save_state(d):
    root=state_root();root.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd,tmp=tempfile.mkstemp(dir=root,prefix='.progress-',text=True)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
        os.replace(tmp,root/'progress.json')
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def home():
    p=state_root()/'isolated-user-files';p.mkdir(parents=True,exist_ok=True);return p
def expanduser(value):
    s=str(value)
    if s=='~':return str(home())
    return str(home()/s[2:]) if s.startswith('~/') else s
def expandpath(value):return Path(expanduser(value))

def getenv(name,default=None):
    # Credentials and contact fields must be explicitly configured for this release.
    if name in ('HOME','USERPROFILE'):return str(home())
    if re.search(r'KEY|TOKEN|SECRET|PASSWORD|EMAIL|ACCOUNT|COOKIE',str(name),re.I):
        value=os.environ.get('RESEARCH_MCP_EXTERNAL_'+str(name),default) if load_state().get('mode')=='login' else default
        if isinstance(value,str) and len(value)>5:_seen_credentials.add(value)
        return value
    return os.environ.get(name,default)

class SafeEnvironment(Mapping):
    def __getitem__(self,key):
        value=getenv(key)
        if value is None:raise KeyError(key)
        return value
    def __iter__(self):
        visible={k for k in os.environ if not re.search(r'KEY|TOKEN|SECRET|PASSWORD|EMAIL|ACCOUNT|COOKIE',k,re.I)}
        visible.update(k[len('RESEARCH_MCP_EXTERNAL_'):] for k in os.environ if k.startswith('RESEARCH_MCP_EXTERNAL_'))
        return iter(visible)
    def __len__(self):return len(list(iter(self)))
    def copy(self):return dict(self)
environment=SafeEnvironment()

def _system_keyring():
    import keyring
    backend=keyring.get_keyring()
    module=type(backend).__module__
    if not any(module.startswith('keyring.backends.'+name) for name in ('Windows','SecretService','kwallet','libsecret','macOS')):
        raise RuntimeError('未找到明确的系统安全存储后端；请配置系统keyring或使用专用环境变量')
    return backend

def credential(provider):
    if load_state().get('mode')!='login':return None
    env=os.environ.get('RESEARCH_MCP_'+provider.upper().replace('-','_')+'_KEY')
    if env:
        _seen_credentials.add(env.strip());return env.strip()
    service='research-mcp-publisher/'+provider
    if sys.platform=='darwin':
        p=subprocess.run(['/usr/bin/security','find-generic-password','-s',service,'-a','research-mcp-user','-w'],capture_output=True,text=True,timeout=15)
        value=p.stdout.strip() if p.returncode==0 else None
        if value:_seen_credentials.add(value)
        return value
    try:
        value=_system_keyring().get_password(service,'research-mcp-user')
        if value:_seen_credentials.add(value)
        return value
    except Exception:return None

def save_credential(provider,value):
    if load_state().get('mode')!='login':raise ValueError('请先选择登录模式 login；一般模式和浙大内网模式不会读取个人凭据')
    if not value or len(value)>4096 or '\n' in value or '\r' in value:raise ValueError('凭据格式无效')
    service='research-mcp-publisher/'+provider
    if sys.platform=='darwin':
        # security's interactive mode keeps the secret out of process arguments.
        if any(c in value for c in ('"','\\')):raise ValueError('此凭据请使用RESEARCH_MCP专用环境变量配置')
        import shlex
        line='add-generic-password -U -s '+shlex.quote(service)+' -a research-mcp-user -w '+shlex.quote(value)+'\n'
        p=subprocess.run(['/usr/bin/security','-i'],input=line,capture_output=True,text=True,timeout=20)
        if p.returncode:raise RuntimeError('系统钥匙串保存失败')
    else:
        _system_keyring().set_password(service,'research-mcp-user',value)

def run(args,*pos,**kwargs):
    global _last_transport_error
    if isinstance(args,(list,tuple)) and args and Path(str(args[0])).name=='security':
        if 'find-generic-password' not in args:raise RuntimeError('发布版不允许旧代码写入系统凭据')
        def option(name):return args[args.index(name)+1] if name in args and args.index(name)+1<len(args) else ''
        service,account=option('-s'),option('-a')
        provider=SERVICES.get(service)
        if service=='zju-research-toolkit':provider={'research-toolkit-elsevier':'elsevier','research-toolkit-cas-common-chemistry':'cas'}.get(account)
        token=credential(provider) if provider else None
        txt=bool(kwargs.get('text') or kwargs.get('universal_newlines') or kwargs.get('encoding'))
        out=(token or '')+ ('\n' if token else '')
        result=subprocess.CompletedProcess(['isolated-credential-read'],0 if token else 44,out if txt else out.encode(),'' if txt else b'')
        if kwargs.get('check') and result.returncode:raise RuntimeError('本用户尚未配置此来源凭据')
        return result
    cmd=list(args) if isinstance(args,(list,tuple)) else args
    if isinstance(cmd,list) and cmd and cmd[0]=='/usr/bin/curl' and sys.platform!='darwin':cmd[0]='curl'
    if isinstance(cmd,list) and cmd and Path(str(cmd[0])).name=='curl' and (len(cmd)<2 or cmd[1]!='-q'):cmd.insert(1,'-q')
    kwargs.setdefault('env',subprocess_environment())
    result=subprocess.run(cmd,*pos,**kwargs)
    if isinstance(cmd,list) and cmd and Path(str(cmd[0])).name=='curl':
        _last_transport_error=None
        if result.returncode in (5,6,7,28,35,60,77):
            from diagnostics import curl_error
            url=next((x for x in cmd if isinstance(x,str) and x.startswith(('https://','http://'))),'')
            if not url:
                config=kwargs.get('input','')
                if isinstance(config,bytes):config=config.decode('utf-8',errors='replace')
                if not isinstance(config,str):config=''
                match=re.search(r'(?m)^url\s*=\s*"([^"\n]+)"',config)
                if match:url=match.group(1)
            _last_transport_error=curl_error(result.returncode,url).as_dict()
    return result

class _RedactingWriter:
    def __init__(self,stream):self.stream=stream
    def write(self,s):
        for value in _seen_credentials:s=s.replace(value,'[REDACTED]')
        return self.stream.write(s)
    def flush(self):return self.stream.flush()
    def __getattr__(self,key):return getattr(self.stream,key)

if os.environ.get('RESEARCH_MCP_ENGINE')=='1':
    sys.stdout=_RedactingWriter(sys.stdout)
    sys.stderr=_RedactingWriter(sys.stderr)
