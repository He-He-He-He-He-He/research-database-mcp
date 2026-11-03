"""Install into a separate per-user runtime. Never write into the source bundle."""
import sys
sys.dont_write_bytecode=True
import argparse,json,os,shutil,subprocess,tempfile,venv,hashlib
from pathlib import Path
from distribution import verify,VERSION

def default_destination():
    base=Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'.local/share'))) if os.name=='nt' else Path.home()/'.local/share'
    return base/'research-database-mcp'

def install(root,destination,mode,config_only=False,extras=False):
    root=Path(root).resolve();destination=Path(destination).expanduser().resolve()
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
        subprocess.run([str(python),'-m','pip','install','-r',str(app/'requirements.txt')],check=True)
        if extras:subprocess.run([str(python),'-m','pip','install','-r',str(app/'requirements-optional.txt')],check=True)
    else:python=Path(sys.executable).absolute()
    os.environ['RESEARCH_MCP_STATE_DIR']=str(state)
    import onboarding
    previous=onboarding.rt.load_state()
    onboarding.select(mode)
    if previous.get('paused'):onboarding.pause(True)
    entry={'command':str(python),'args':['-B',str(app/'research_mcp.py')],'env':{'RESEARCH_MCP_STATE_DIR':str(state),'PYTHONDONTWRITEBYTECODE':'1'}}
    config={'mcpServers':{'research-databases':entry}}
    connection=destination/'connection';connection.mkdir(exist_ok=True)
    config_path=connection/'mcp-config.json';config_path.write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
    toml='[mcp_servers.research-databases]\ncommand = '+json.dumps(str(python),ensure_ascii=False)+'\nargs = '+json.dumps(entry['args'],ensure_ascii=False)+'\nenv = '+'{'+', '.join(json.dumps(k)+' = '+json.dumps(v,ensure_ascii=False) for k,v in entry['env'].items())+'}'+'\n'
    (connection/'mcp-config.codex.toml').write_text(toml,encoding='utf-8')
    # The JSON result is intended for this recipient's AI; it is not a release file.
    return {'installed':True,'version':VERSION,'mode':mode,'connection_file':str(config_path),'codex_connection_file':str(connection/'mcp-config.codex.toml'),'mcp_entry':entry,'runtime_app':str(app),'progress_location':str(state),'source_unchanged':True,'next':'只把本服务追加到当前AI客户端支持的MCP配置；不要打印原有连接器密钥。连接后调用research_setup(status/next)，工具应有5个。'}

def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    p=argparse.ArgumentParser(description='安装在用户独立目录，发行包保持干净')
    p.add_argument('--mode',choices=['partial','full']);p.add_argument('--install-dir',type=Path,default=default_destination())
    p.add_argument('--config-only',action='store_true');p.add_argument('--extras',action='store_true');a=p.parse_args()
    if sys.version_info<(3,10):raise SystemExit('需要Python 3.10或更新版本')
    mode=a.mode
    if mode is None and sys.stdin.isatty():
        choice=input('请选择：1 部分功能（免登录） / 2 全部可选功能（可暂停）[1]：').strip()
        if choice not in ('','1','2'):raise SystemExit('未选择有效模式')
        mode='full' if choice=='2' else 'partial'
    if not mode:raise SystemExit('请先询问用户partial/full，再通过--mode传入选择')
    print(json.dumps(install(Path(__file__).resolve().parent,a.install_dir,mode,a.config_only,a.extras),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
