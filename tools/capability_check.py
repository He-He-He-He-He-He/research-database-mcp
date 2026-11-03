"""Opt-in public samples: execution, nonempty records and numbers are separate."""
import _bootstrap
import argparse,base64,json,os,tempfile,time,zlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import onboarding
from research_cli import query

CASES=[
 ('cbs-no-match','cbs-datasets',['--query','population','--top','2'],'empty_result'),
 ('cbs-dutch-catalog','cbs-datasets',['--query','Bevolking','--top','2'],'records'),
 ('cbs-properties','cbs-properties',['03743'],'metadata'),
 ('cbs-dimensions','cbs-dimensions',['03743'],'records'),
 ('cbs-measures','cbs-codes',['03743','--dimension','Measure','--top','1'],'records'),
 ('cbs-values','cbs-observations',['03743','--top','2'],'numbers'),
 ('census','us-census-popest-2024',['United States','--year','2024','--limit','1'],'numbers'),
 ('treasury','us-treasury-debt',['--start','2024-01-02','--end','2024-01-03','--page-size','2'],'numbers'),
 ('eurostat','eurostat',['demo_pjan','DE','2023','--filter','sex=T','--filter','age=TOTAL'],'numbers'),
 ('adb','adb-series',['DF_PPSI_POP','LP_PE_NUM_MOP','PRC','2022','2023'],'numbers'),
 ('fda-label','fda-drug-labels',['ibuprofen','--limit','1'],'records'),
 ('iadb-catalog','iadb-search',['population','--limit','1'],'records'),
 ('who-tb','who-tb',['estimates','--iso3','EGY','--year','2023','--limit','1'],'numbers'),
 ('who-ghed','who-ghed-data',['EGY','che_gdp','2022','2022'],'numbers'),
 ('who-air','who-air-quality-2026',['EGY','--limit','1'],'numbers'),
 ('iarc-estimates','iarc-globocan-rates',['818','--year','2022'],'numbers'),
]

def check(case):
    label,command,args,expect=case;start=time.monotonic()
    result=query(command,args,output='full',timeout=100)
    status=result.get('result_status')
    accepted=bool(result.get('ok'))
    if expect=='empty_result':
        accepted=accepted and status=='empty_result' and result.get('has_records') is False
    elif expect=='numbers':accepted=accepted and result.get('data_verified') is True
    elif expect=='records':accepted=accepted and result.get('has_records') is True
    elif expect=='metadata':accepted=accepted and bool(result.get('result'))
    row={'check':label,'command':command,'args':args,'expected':expect,'accepted':bool(accepted),'seconds':round(time.monotonic()-start,2)}
    for key in ('ok','execution_ok','error','result_kind','result_status','has_records','has_content','has_data','content_level','record_count','numeric_observation_count','data_verified','empty_reason'):
        if key in result:row[key]=result[key]
    if command=='cbs-datasets':row['query_info']=result.get('result',{}).get('query_info')
    print(json.dumps(row,ensure_ascii=False),flush=True)
    return row

def main():
    p=argparse.ArgumentParser(description='公开能力抽样；不读取用户凭据，不输出正文或数据行。零命中样例通过不等于获得数据。')
    p.add_argument('--suite',choices=['cbs','all'],default='cbs');p.add_argument('--output',type=Path);p.add_argument('--allow-failures',action='store_true');a=p.parse_args()
    root=Path(__file__).resolve().parent.parent
    if a.output and a.output.expanduser().resolve().is_relative_to(root):p.error('输出必须位于发行目录外')
    original=os.environ.get('RESEARCH_MCP_STATE_DIR')
    try:
        with tempfile.TemporaryDirectory(prefix='research-capability-check-') as state:
            os.environ['RESEARCH_MCP_STATE_DIR']=state;onboarding.select('general')
            cases=CASES[:6] if a.suite=='cbs' else CASES
            with ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(check,cases))
            report={'suite':a.suite,'credentials_used':False,'environment':'isolated general mode; current process network','accepted':sum(x['accepted'] for x in rows),'total':len(rows),'numeric_samples':sum(x.get('data_verified') is True for x in rows),'nonempty_record_samples':sum(x.get('has_records') is True for x in rows),'expected_empty_samples':sum(x['accepted'] and x['expected']=='empty_result' for x in rows),'checks':rows,'note':'acceptance按每项预期判断；预期零命中、目录、标签、估计值与数值分别记录，不计作全文权限或全库验收。'}
            if a.output:
                a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False))
            if os.environ.get('GITHUB_ACTIONS')=='true':
                payload=base64.b64encode(zlib.compress(json.dumps(report,ensure_ascii=False).encode(),9)).decode()
                print('::notice title=Capability validation report (zlib-base64)::'+payload)
            return 0 if a.allow_failures or report['accepted']==report['total'] else 1
    finally:
        if original is None:os.environ.pop('RESEARCH_MCP_STATE_DIR',None)
        else:os.environ['RESEARCH_MCP_STATE_DIR']=original
if __name__=='__main__':raise SystemExit(main())
