"""Manifest-only distribution operations. No filesystem snapshots are exported."""
import hashlib
from pathlib import Path, PurePosixPath

VERSION = '1.1.1'
ARCHIVE_ROOT = '研究数据库MCP_发布整理版'
BLOCKED_PARTS = {'.venv','venv','__pycache__','pycache','__MACOSX','.git','.cache'}
ROOT_FILES = {'CHANGELOG.md','README.md','00_发给自己的AI.md','AGENTS.md','AI安装指南.md','功能边界与隐私.md','验收说明.md','.gitignore','distribution.py','install.py','pack_release.py','verify_manifest.py','release_runtime.py','research_cli.py','research_mcp.py','onboarding.py','cas_bridge.py','self_check.py','test_distribution.py','requirements.txt','requirements-optional.txt','command_catalog.json','build_inventory.json','starter_examples.json'}

DOC_FILES = {'docs/QUICKSTART.md','docs/EXAMPLES.md','docs/DATA_SOURCES.md','docs/CONFIGURATION.md','docs/TROUBLESHOOTING.md','docs/ARCHITECTURE.md'}

def permitted(name):
    p=PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or any(x in BLOCKED_PARTS for x in p.parts) or '\\' in name:return False
    if name in DOC_FILES:return True
    if len(p.parts)==1:return name in ROOT_FILES
    return p.parts[0]=='engine' and p.suffix in ('.py','.mjs')

def entries(root):
    manifest=root/'MANIFEST.sha256'
    if manifest.is_symlink():raise ValueError('清单不能是符号链接')
    found={}
    for line in manifest.read_text(encoding='utf-8').splitlines():
        digest,name=line.split('  ',1)
        if len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest) or not permitted(name) or name in found:raise ValueError('发行清单格式或文件类型无效')
        found[name]=digest
    return found

def verify(root,strict=True):
    root=Path(root).resolve();files=entries(root);errors=[]
    for name,digest in files.items():
        p=root/name
        if p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(root):errors.append('missing_or_unsafe:'+name)
        elif hashlib.sha256(p.read_bytes()).hexdigest()!=digest:errors.append('changed:'+name)
    extra=[str(p.relative_to(root)) for p in root.rglob('*') if (p.is_file() or p.is_symlink()) and str(p.relative_to(root)) not in files and str(p.relative_to(root))!='MANIFEST.sha256']
    if strict and extra:errors.append('unlisted_runtime_or_other_files:'+str(len(extra)))
    return {'ok':not errors,'files':len(files),'extra_files':len(extra),'errors':errors},files
