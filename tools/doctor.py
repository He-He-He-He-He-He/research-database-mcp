"""Redacted runtime diagnosis; no environment values or credentials are printed."""
import sys
import _bootstrap
sys.dont_write_bytecode=True
import argparse,json
from diagnostics import environment_summary
from research_cli import query

def query_diagnosis(result):
    # A compact query may contain a real data preview or local export paths.
    # Diagnostic output has an explicit allowlist rather than an exclusion list.
    fields=('ok','command','error','message','diagnostics','result_status','execution_ok','record_count','has_records','has_content','has_data','content_level','numeric_observation_count','data_verified','empty_reason','skipped','required_mode','hint')
    out={key:result[key] for key in fields if key in result}
    if result.get('ok'):out['response_type']=type(result['result']).__name__ if 'result' in result else 'exported_or_no_inline_result'
    return out

def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    p=argparse.ArgumentParser(description='检查当前 MCP 运行环境，或复现一条实际查询')
    p.add_argument('--command');p.add_argument('--args-json',default='[]')
    a=p.parse_args();out={'environment':environment_summary()}
    if a.command:
        try:args=json.loads(a.args_json)
        except ValueError:p.error('--args-json 必须是有效的 JSON 字符串数组')
        result=query(a.command,args)
        # Report health and diagnostics, not the research content itself.
        out['query']=query_diagnosis(result)
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return 0 if not a.command or out['query'].get('ok') else 1
if __name__=='__main__':sys.exit(main())
