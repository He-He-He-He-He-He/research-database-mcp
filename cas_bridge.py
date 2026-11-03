import sys
sys.dont_write_bytecode=True
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'engine'))
import cas_common_chemistry_adapter as cas
def main():
    from diagnostics import CommandParser
    p=CommandParser();s=p.add_subparsers(dest='command',required=True)
    x=s.add_parser('cas-common-search');x.add_argument('query');x.add_argument('--size',type=int,default=5);x.add_argument('--offset',type=int,default=0)
    x=s.add_parser('cas-common-detail');x.add_argument('casrn')
    a=p.parse_args()
    import os
    if os.environ.get('RESEARCH_MCP_VALIDATE_ONLY')=='1':
        print(json.dumps({'ok':True,'validation_only':True}));return
    result=cas.search(a.query,a.size,a.offset) if a.command=='cas-common-search' else cas.detail(a.casrn)
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except Exception as exc:
        from diagnostics import error_payload,InvalidArguments
        print(json.dumps(error_payload(exc),ensure_ascii=False),file=sys.stderr)
        sys.exit(2 if isinstance(exc,InvalidArguments) else 1)
