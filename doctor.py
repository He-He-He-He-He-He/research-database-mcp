"""Redacted runtime diagnosis; no environment values or credentials are printed."""
import sys
sys.dont_write_bytecode=True
import argparse,json
from diagnostics import environment_summary
from research_cli import query

def main():
    p=argparse.ArgumentParser(description='检查当前 MCP 运行环境，或复现一条实际查询')
    p.add_argument('--command');p.add_argument('--args-json',default='[]')
    a=p.parse_args();out={'environment':environment_summary()}
    if a.command:
        try:args=json.loads(a.args_json)
        except ValueError:p.error('--args-json 必须是有效的 JSON 字符串数组')
        result=query(a.command,args)
        # Report health and diagnostics, not the research content itself.
        out['query']={k:v for k,v in result.items() if k not in ('result','requirements')}
        if result.get('ok'):out['query']['response_type']=type(result.get('result')).__name__
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return 0 if not a.command or out['query'].get('ok') else 1
if __name__=='__main__':sys.exit(main())
