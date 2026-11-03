"""Export an allowlisted, reproducible ZIP. Never include installed state."""
import sys
sys.dont_write_bytecode=True
import argparse,json,os,tempfile,zipfile
from pathlib import Path
from distribution import verify,ARCHIVE_ROOT

def pack(root,output,replace=False):
    root=Path(root).resolve();output=Path(output).expanduser().resolve()
    if output.is_relative_to(root):raise ValueError('压缩包必须保存在发行文件夹外')
    if output.exists() and not replace:raise ValueError('目标ZIP已存在；请另选路径，或明确使用--replace')
    result,files=verify(root,strict=False)
    if not result['ok']:raise ValueError('清单文件缺失或被修改，停止打包')
    output.parent.mkdir(parents=True,exist_ok=True)
    fd,temporary=tempfile.mkstemp(prefix='.release-',suffix='.zip',dir=output.parent);os.close(fd)
    try:
        with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for name in sorted([*files,'MANIFEST.sha256']):
                info=zipfile.ZipInfo(ARCHIVE_ROOT+'/'+name,date_time=(2026,1,1,0,0,0))
                info.create_system=3;info.external_attr=0o100644<<16;info.compress_type=zipfile.ZIP_DEFLATED
                z.writestr(info,(root/name).read_bytes())
        os.replace(temporary,output)
    finally:
        if os.path.exists(temporary):os.unlink(temporary)
    return {'ok':True,'zip':str(output),'files':len(files)+1,'excluded_unlisted_files':result['extra_files'],'note':'ZIP仅含清单文件，不含虚拟环境、生成配置、进度、缓存或macOS附加元数据。'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path);p.add_argument('--replace',action='store_true');a=p.parse_args()
    root=Path(__file__).resolve().parent
    print(json.dumps(pack(root,a.output or root.parent/(ARCHIVE_ROOT+'.zip'),a.replace),ensure_ascii=False,indent=2))
