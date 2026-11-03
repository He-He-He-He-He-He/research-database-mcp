"""Explicit-client JSON merging. Never inventory other apps or print their data."""
import json,os,sys,tempfile,uuid
from pathlib import Path
import release_runtime as rt

def location(client):
    if client=='cursor':return Path.home()/'.cursor/mcp.json'
    if client=='copilot':return Path(os.environ.get('COPILOT_HOME',str(Path.home()/'.copilot')))/'mcp-config.json'
    if client=='claude-desktop':
        if sys.platform=='darwin':return Path.home()/'Library/Application Support/Claude/claude_desktop_config.json'
        if sys.platform=='win32':return Path(os.environ.get('APPDATA',str(Path.home()/'AppData/Roaming')))/'Claude/claude_desktop_config.json'
    raise ValueError('此客户端请显式提供 --client-config，不扫描其他应用')

def merge(entry,client='generic',path=None,replace_existing=False):
    target=Path(path).expanduser() if path else location(client)
    if target.is_symlink():raise ValueError('配置文件为符号链接，请核对真实文件后显式提供路径')
    target=target.absolute();raw=target.read_bytes() if target.exists() else None
    try:document=json.loads(raw.decode('utf-8-sig')) if raw is not None else {}
    except (ValueError,UnicodeError):raise ValueError('配置不是严格JSON（可能含注释）；已保留原文件，请用客户端界面合并生成的片段') from None
    if not isinstance(document,dict):raise ValueError('客户端配置根节点须为对象，未写入')
    field='servers' if client=='vscode' else 'mcpServers'
    servers=document.setdefault(field,{})
    if not isinstance(servers,dict):raise ValueError('客户端服务列表格式异常，未写入')
    old=servers.get('research-databases')
    if old is not None and not isinstance(old,dict):raise ValueError('已有同名服务格式异常，未覆盖')
    if old and old!=entry and not replace_existing:
        same_state=isinstance(old.get('env'),dict) and old['env'].get('RESEARCH_MCP_STATE_DIR')==entry.get('env',{}).get('RESEARCH_MCP_STATE_DIR')
        same_python=old.get('command')==entry.get('command')
        if not (same_state and same_python):raise ValueError('已有不同的同名服务，未覆盖；核对后可用 --replace-client-entry 显式替换此服务')
    merged={**(old or {}),**entry,'env':{**((old or {}).get('env') or {}),**entry.get('env',{})}}
    if client=='vscode':merged['type']='stdio'
    if old==merged:return {'written':False,'unchanged':True,'client':client,'config_file':str(target),'connected':False,'next':'客户端需重连并看到7个工具后才算接入'}
    backup=None
    if raw is not None:
        folder=rt.state_root()/'client-backups';folder.mkdir(parents=True,exist_ok=True,mode=0o700)
        backup=folder/(uuid.uuid4().hex+'.json');backup.write_bytes(raw);os.chmod(backup,0o600)
    servers['research-databases']=merged
    target.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(dir=target.parent,prefix='.research-mcp-',text=True)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            json.dump(document,stream,ensure_ascii=False,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
        os.replace(name,target)
    finally:
        if os.path.exists(name):os.unlink(name)
    return {'written':True,'client':client,'config_file':str(target),'backup_file':str(backup) if backup else None,'connected':False,'next':'只写入了本服务配置；请重连客户端，核对7个工具及实际查询'}
