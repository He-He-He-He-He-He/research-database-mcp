"""Strict verification: unlisted runtime files now fail the shareability check."""
import sys
sys.dont_write_bytecode=True
import json
from pathlib import Path
from distribution import verify

if __name__=='__main__':
    result,_=verify(Path(__file__).resolve().parent,strict=True)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if not result['ok']:print('请用pack_release.py导出仅含清单文件的干净ZIP；不要直接压缩安装目录。')
    raise SystemExit(0 if result['ok'] else 1)
