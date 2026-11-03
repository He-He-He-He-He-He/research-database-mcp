"""Install into a separate per-user runtime. Never write into the source bundle."""
import sys
sys.dont_write_bytecode=True
import argparse,json,os,shutil,subprocess,tempfile,venv,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from distribution import verify,VERSION
import access_policy as policy

def default_destination():
    base=Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'.local/share'))) if os.name=='nt' else Path.home()/'.local/share'
    return base/'research-database-mcp'

def install(root,destination,mode,config_only=False,extras=False,index_url=None,fallback_index_url=None,client=None,client_config=None,replace_client_entry=False):
    from install_network import validate_index,dependencies
    validate_index(index_url);validate_index(fallback_index_url)
    mode=policy.normalize(mode)
    root=Path(root).resolve();destination=Path(destination).expanduser().resolve()
    if client or client_config:
        from client_connect import location
        selected=Path(client_config).expanduser() if client_config else location(client)
        if selected.resolve().is_relative_to(root):raise ValueError('客户端配置不能写入原始发行文件夹')
    if destination.is_relative_to(root):raise ValueError('安装目录必须在发行文件夹之外')
    result,files=verify(root,strict=False)
    if not result['ok']:raise ValueError('原始代码清单校验失败，未安装')
    state=Path(os.environ.get('RESEARCH_MCP_STATE_DIR',str(destination/'state'))).expanduser().resolve()
    if state.is_relative_to(root):raise ValueError('进度目录不能放在发行文件夹中')
    destination.mkdir(parents=True,exist_ok=True,mode=0o700)
    fingerprint=hashlib.sha256((root/'MANIFEST.sha256').read_bytes()).hexdigest()[:12]
    app=destination/'apps'/(VERSION+'-'+fingerprint)
    if app.exists():
        current,_=verify(app,strict=False)
        if not current['ok']:raise ValueError('已安装的同版本代码被修改，请保留并选择其他安装目录')
    else:
        app.parent.mkdir(exist_ok=True)
        temp=Path(tempfile.mkdtemp(prefix='.install-',dir=app.parent))
        try:
            for name in [*files,'MANIFEST.sha256']:
                p=temp/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/name,p)
            temp.rename(app)
        finally:
            if temp.exists():shutil.rmtree(temp)
    folder=destination/'runtime-venv'
    if not config_only:
        if not folder.exists():venv.EnvBuilder(with_pip=True).create(folder)
        python=folder/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
        dependencies(python,app/'src/requirements.txt',index_url,fallback_index_url)
        if extras:dependencies(python,app/'src/requirements-optional.txt',index_url,fallback_index_url)
    else:python=Path(sys.executable).absolute()
    os.environ['RESEARCH_MCP_STATE_DIR']=str(state)
    import onboarding
    previous=onboarding.rt.load_state()
    if mode is None:mode=previous.get('mode') or 'general'
    onboarding.select(mode)
    if previous.get('paused'):onboarding.pause(True)
    entry={'command':str(python),'args':['-B',str(app/'src/research_mcp.py')],'env':{'RESEARCH_MCP_STATE_DIR':str(state),'PYTHONDONTWRITEBYTECODE':'1'}}
    config={'mcpServers':{'research-databases':entry}}
    connection=destination/'connection';connection.mkdir(exist_ok=True)
    config_path=connection/'mcp-config.json';config_path.write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
    toml='[mcp_servers.research-databases]\ncommand = '+json.dumps(str(python),ensure_ascii=False)+'\nargs = '+json.dumps(entry['args'],ensure_ascii=False)+'\nenv = '+'{'+', '.join(json.dumps(k)+' = '+json.dumps(v,ensure_ascii=False) for k,v in entry['env'].items())+'}'+'\n'
    (connection/'mcp-config.codex.toml').write_text(toml,encoding='utf-8')
    (connection/'sdk-settings.json').write_text(json.dumps({'state_dir':str(state)},ensure_ascii=False),encoding='utf-8')
    if not config_only:
        purelib=subprocess.run([str(python),'-c','import sysconfig;print(sysconfig.get_path("purelib"))'],capture_output=True,text=True,check=True).stdout.strip()
        lib=Path(purelib).resolve()
        if not lib.is_relative_to(folder.resolve()):raise ValueError('SDK导入目录不属于本工具虚拟环境，未写入')
        (lib/'research_database_mcp.pth').write_text('import sys; sys.path.insert(0, '+ascii(str(app/"src"))+')\n',encoding='ascii')
    client_result=None
    if client or client_config:
        from client_connect import merge
        client_result=merge(entry,client or 'generic',client_config,replace_client_entry)
    # The JSON result is intended for this recipient's AI; it is not a release file.
    return {'installed':True,'version':VERSION,'mode':mode,'connection_file':str(config_path),'codex_connection_file':str(connection/'mcp-config.codex.toml'),'mcp_entry':entry,'runtime_app':str(app),'progress_location':str(state),'source_unchanged':True,'sdk_importable_in_runtime_venv':not config_only,'client':client_result,'next':'只把本服务追加到指定客户端，不打印已有连接器密钥；重连后核对7个工具和实际查询。SDK使用此虚拟环境Python导入research_sdk。'}

def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    p=argparse.ArgumentParser(description='安装在用户独立目录，发行包保持干净')
    p.add_argument('--mode',choices=[*policy.MODES,*policy.ALIASES]);p.add_argument('--install-dir',type=Path,default=default_destination())
    p.add_argument('--config-only',action='store_true');p.add_argument('--extras',action='store_true')
    p.add_argument('--index-url');p.add_argument('--fallback-index-url')
    p.add_argument('--client',choices=['cursor','copilot','claude-desktop','vscode','generic']);p.add_argument('--client-config',type=Path);p.add_argument('--replace-client-entry',action='store_true');a=p.parse_args()
    if sys.version_info<(3,10):raise SystemExit('需要Python 3.10或更新版本')
    mode=a.mode
    # New installs default to general; upgrades without --mode keep their choice.
    if a.client in ('generic','vscode') and not a.client_config:p.error('此客户端须显式提供--client-config')
    print(json.dumps(install(Path(__file__).resolve().parent,a.install_dir,mode,a.config_only,a.extras,a.index_url,a.fallback_index_url,a.client,a.client_config,a.replace_client_entry),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
