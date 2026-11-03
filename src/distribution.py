"""Manifest-only distribution operations. No filesystem snapshots are exported."""
import hashlib
from pathlib import Path, PurePosixPath

VERSION = '1.5.0'
ARCHIVE_ROOT = '研究数据库MCP_发布整理版'
BLOCKED_PARTS = {'.venv','venv','__pycache__','pycache','__MACOSX','.git','.cache'}
ROOT_FILES = {'README.md', '.gitattributes', 'AGENTS.md', '.gitignore', 'install.py'}

PACKAGE_FILES = {'docs/INSTALL.md', 'tests/_bootstrap.py', 'src/research_sdk.py', 'docs/PRIVACY.md', 'docs/CHANGELOG.md', 'docs/ARCHITECTURE.md', 'docs/AI_HANDOFF.md', 'docs/QUICKSTART.md', 'docs/PRODUCTIVITY.md', 'src/network_health.py', 'tools/doctor.py', 'tools/verify_manifest.py', 'src/install_network.py', 'docs/TROUBLESHOOTING.md', 'src/cas_bridge.py', 'src/requirements.txt', 'src/research_mcp.py', 'tests/test_core.py', 'docs/DATA_SOURCES.md', 'tools/public_check.py', 'tests/test_access_modes.py', 'src/access_policy.py', 'src/diagnostics.py', 'src/result_store.py', 'src/release_runtime.py', 'tools/_bootstrap.py', 'src/batch_query.py', 'tools/build_access_catalog.py', 'src/distribution.py', 'src/requirements-optional.txt', 'docs/ACCEPTANCE.md', 'src/client_connect.py', 'src/data/command_catalog.json', 'src/data/build_inventory.json', 'docs/EXAMPLES.md', 'tests/test_distribution.py', 'tools/pack_release.py', 'src/research_cli.py', 'docs/VALIDATION.md', 'tests/test_diagnostics.py', 'docs/CONFIGURATION.md', 'src/onboarding.py', '.github/workflows/quality.yml', 'src/data/starter_examples.json', 'tests/test_productivity.py'}

PACKAGE_FILES.update({'src/result_contracts.py','src/capabilities.py','src/data/verified_capabilities.json','tests/test_result_contracts.py','tools/capability_check.py','docs/CAPABILITIES.md'})

def permitted(name):
    p=PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or any(x in BLOCKED_PARTS for x in p.parts) or '\\' in name:return False
    if name in ROOT_FILES or name in PACKAGE_FILES:return True
    return len(p.parts)>2 and p.parts[:2]==('src','engine') and p.suffix in ('.py','.mjs')

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
    extra=[p.relative_to(root).as_posix() for p in root.rglob('*') if (p.is_file() or p.is_symlink()) and p.relative_to(root).as_posix() not in files and p.relative_to(root).as_posix()!='MANIFEST.sha256']
    if strict and extra:errors.append('unlisted_runtime_or_other_files:'+str(len(extra)))
    return {'ok':not errors,'files':len(files),'extra_files':len(extra),'errors':errors},files
