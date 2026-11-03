"""Opt-in public endpoint checks. Outputs status, never research rows or secrets."""
import sys
sys.dont_write_bytecode=True
import argparse,base64,json,math,os,tempfile,time,zlib
from pathlib import Path
from diagnostics import environment_summary
import release_runtime as rt
import onboarding
from research_cli import query

QUICK=[('worldbank','wb-series',['FRA','SP.POP.TOTL','--start','2020','--end','2023']),('crossref','crossref',['renewable energy','--rows','1']),('arxiv','arxiv',['digital economy','--size','1']),('pubmed','pubmed-search',['digital economy','--size','1']),('ons','ons-dataset-discover',['population','--max-pages','1','--limit','1']),('cbs','cbs-datasets',['--top','1']),('faostat','faostat-api-domains',['--limit','1']),('bis','bis-dataflows',['exchange']),('usgs','usgs-earthquakes',['2024-01-01','2024-01-02','--limit','1']),('law','law-search',['消费者权益保护法','--size','1']),('nbs-reports','nbs-macro-list',['--page','1']),('spp','spp-reports',[]),('nasa','nasa-power-daily',['0','0','2024-01-01','2024-01-02'])]
CHINA=[('gdp','国内生产总值','annual','2020','2023'),('cpi','居民消费价格指数','monthly','2024-01','2024-03'),('ppi','工业生产者出厂价格指数','monthly','2024-01','2024-03'),('pmi','制造业采购经理指数','monthly','2024-01','2024-03'),('retail','社会消费品零售总额','monthly','2024-01','2024-03')]

def count_rows(value):
    if isinstance(value,list):return len(value[1]) if len(value)==2 and isinstance(value[1],list) else len(value)
    if not isinstance(value,dict):return None
    if isinstance(value.get('message'),dict) and isinstance(value['message'].get('items'),list):return len(value['message']['items'])
    if isinstance(value.get('esearchresult'),dict):return len(value['esearchresult'].get('idlist',[]))
    for key in ('items','rows','value','dataflows','candidates','data'):
        if isinstance(value.get(key),list):return len(value[key])
    return None

def brief(label,command,result,elapsed):
    out={'check':label,'command':command,'ok':result.get('ok',False),'seconds':round(elapsed,2),'result_kind':result.get('result_kind')}
    if result.get('ok'):out['returned_rows']=count_rows(result.get('result'));out['partial']=result.get('partial',False)
    else:
        for key in ('error','message','diagnostics'):out[key]=result.get(key)
    return out

def china_case(label,keyword,frequency,start,end):
    began=time.monotonic()
    found=query('nbs-frequency-discover',[keyword,frequency,'--size','20'])
    if not found.get('ok'):return brief(label,'nbs-frequency-discover',found,time.monotonic()-began)
    rows=found['result'].get('candidates',[])
    needle=found['result'].get('search_keyword',keyword)
    candidates=[x for x in rows if x.get('region_code')=='000000000000' and needle in str(x.get('name',''))]
    if not candidates:return {'check':label,'command':'nbs-frequency-discover','ok':False,'error':'no_matching_national_candidate','seconds':round(time.monotonic()-began,2)}
    expected=[x for x in candidates if str(x.get('name','')).strip().startswith(needle)]
    if not expected:return {'check':label,'command':'nbs-frequency-discover','ok':False,'error':'no_expected_name_prefix','related_candidates':len(candidates),'seconds':round(time.monotonic()-began,2)}
    candidate=expected[0]
    args=[candidate['catalog_id'],candidate['indicator_id'],candidate['root_id'],frequency,start,end,'--region-code',candidate['region_code'],'--region-name',candidate.get('region_name') or '全国']
    result=query('nbs-frequency-series',args)
    out=brief(label,'nbs-frequency-series',result,time.monotonic()-began)
    if result.get('ok'):
        data=result['result'];points=data.get('data',[]);values=[v.get('value') for row in points for v in row.get('values',[])]
        def numeric(value):
            try:return value is not None and math.isfinite(float(str(value).replace(',','')))
            except (TypeError,ValueError):return False
        out.update(indicator=candidate['name'],frequency=frequency,periods=[x.get('code') for x in points],numeric_observations=sum(numeric(x) for x in values))
        if not out['numeric_observations']:out.update(ok=False,error='no_numeric_observations')
    return out

def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    p=argparse.ArgumentParser(description='可选联网抽样：只使用公开来源，不读取实际用户配置或凭据')
    p.add_argument('--suite',choices=['quick','china','modes','all'],default='quick');p.add_argument('--output',type=Path);p.add_argument('--allow-failures',action='store_true');a=p.parse_args()
    root=Path(__file__).resolve().parent
    if a.output and a.output.expanduser().resolve().is_relative_to(root):raise SystemExit('诊断输出必须位于发行目录外')
    original=os.environ.get('RESEARCH_MCP_STATE_DIR')
    try:
        with tempfile.TemporaryDirectory(prefix='research-public-check-') as state:
            os.environ['RESEARCH_MCP_STATE_DIR']=state;onboarding.select('general');rows=[]
            if a.suite in ('quick','all'):
                for label,command,args in QUICK:
                    began=time.monotonic();out=brief(label,command,query(command,args),time.monotonic()-began);rows.append(out);print(json.dumps(out,ensure_ascii=False),flush=True)
            if a.suite in ('modes','all'):
                cases=[('public-extension-datacite','datacite',['renewable energy','--size','1']),
                       ('public-extension-epmc','epmc',['renewable energy','--size','1']),
                       ('public-extension-journalism','journalism-crossref',['digital','--page-size','1']),
                       ('public-extension-nbs-household','household-spending-groups',[])]
                for label,command,args in cases:
                    began=time.monotonic();out=brief(label,command,query(command,args),time.monotonic()-began);rows.append(out);print(json.dumps(out,ensure_ascii=False),flush=True)
            if a.suite in ('china','all'):
                for case in CHINA:
                    out=china_case(*case);rows.append(out);print(json.dumps(out,ensure_ascii=False),flush=True)
            report={'environment':environment_summary(),'suite':a.suite,'credential_mode':'isolated general; no saved user credentials','passed':sum(x['ok'] for x in rows),'total':len(rows),'checks':rows,'note':'仅证明这些样例请求的状态，不代表全部起步命令、参数、数据范围或其他运行环境均可用。'}
            if a.output:
                a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
            print(json.dumps({'passed':report['passed'],'total':report['total']},ensure_ascii=False))
            if os.environ.get('GITHUB_ACTIONS')=='true':
                notice=base64.b64encode(zlib.compress(json.dumps(report,ensure_ascii=False).encode('utf-8'),9)).decode('ascii')
                print('::notice title=Public validation report (zlib-base64)::'+notice)
            return 0 if a.allow_failures or report['passed']==report['total'] else 1
    finally:
        if original is None:os.environ.pop('RESEARCH_MCP_STATE_DIR',None)
        else:os.environ['RESEARCH_MCP_STATE_DIR']=original
if __name__=='__main__':sys.exit(main())
