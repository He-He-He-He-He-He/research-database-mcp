"""Separate successful execution, matching records, and numeric observations.

Only declared measure fields are counted. IDs, dates and total counts are never
used as evidence that an observations command returned statistical values.
"""
import math

MEASURES={
 'wb-series':['1.*.value'],
 'wto-timeseries':['response.Dataset.*.Value'],
 'cbs-observations':['value.*.Value'],
 'nbs-annual-series':['data.*.values.*.value'],
 'nbs-frequency-series':['data.*.values.*.value'],
 'household-spending':['data.*.values.*.value'],
 'eurostat':['value.*'], 'eurostat-multi':['value.*'],
 'us-treasury-debt':['items.*.tot_pub_debt_out_amt'],
 'us-census-popest-2024':['items.*.population_estimate.*'],
 'who-ghed-data':['records.*.value'],
 'who-tb':['records.*.e_inc_100k'],
 'usgs-earthquakes':['items.*.magnitude'],
 'nasa-power-daily':['raw_parameter_values.*.*'],
 'ons-observations':['observations.*.observation'],
 'adb-series':['observations.*.OBS_VALUE'],
 'idb-social-data':['data.records.*.value'],
 'iarc-globocan-rates':['response.dataset.*.asr','response.dataset.*.total','response.dataset.*.crude_rate'],
 'who-air-quality-2026':['records.*.pm25_concentration'],
}

TEXT_FIELDS={
 'drcnet-institution-article':('article_text',['text']),
 'drcnet-search-article':('article_text',['article.text']),
 'rdfybk-institution-content':('reader_segments',['segments.*']),
 'dingxiu-institution-page':('single_page_text',['page_html']),
 'tianlu-institution-page':('single_page_text',['main_text_raw']),
 'infobank-institution-article':('article_text',['paragraphs.*']),
 'minguofy-institution-document':('article_text',['paragraphs.*.text']),
 'minguofy-institution-content-hits':('snippet',['items.*.snippet_raw_html']),
}

# Templates bind source fields verbatim. They are instructions for one selected
# record, not proof that the next request or all pages will be authorized.
FOLLOWUPS={
 'rdfybk-institution-catalog':{'command':'rdfybk-institution-content','args':['{id}','{title}','--page','1']},
 'dingxiu-institution-catalog':{'command':'dingxiu-institution-page','args':['{guid}','{title_traditional}','--page','1']},
 'tianlu-ip-catalog':{'command':'tianlu-institution-page','args':['{id}','{title}','--page','1']},
 'infobank-search':{'command':'infobank-institution-article','args':['{record_id}','{database}','{partition}','--expected-title','{title}']},
 'hbn-institution-indicators':{'command':'hbn-institution-values','args':['{dbid}','{code}','<YYYY-MM-DD start>','<YYYY-MM-DD end>'],'note':'日期由研究问题指定；原值与预测/实绩状态、单位仍需核对。'},
 'drcnet-ip-search':{'command':'drcnet-institution-article','args':['{detail_reference.doc_id}','{detail_reference.leaf_id}','{detail_reference.channel_id}','{detail_reference.expected_title}'],'note':'使用已解析的detail_reference；完整chnidPath不是数字频道号。原始路径仍保留供核对。'},
 'minguofy-institution-content-hits':{'command':'minguofy-institution-document','args':['{source_query}','{result_offset}','{title}'],'note':'位置是搜索结果起始位置，不是文件内偏移；详情会重新定位并逐字核对题名。'},
 'nmrdata-institution-catalog':{'command':'nmrdata-institution-spectrum','args':['{record_id}','{compound_name}'],'note':'仅谱表；目录身份/关键词校验未通过时不得继续猜测记录号。'},
 'cbs-datasets':{'command':'cbs-properties','args':['{Identifier}'],'note':'先查看Properties、Dimensions和cbs-codes，再用真实维度代码调用cbs-observations。'},
}

def enrich(entry):
    """Curated expectations, never a replacement for actual sample evidence."""
    command=entry['command'];kind=entry.setdefault('result_kind','unclassified')
    level=TEXT_FIELDS.get(command, (None,))[0]
    if command in TEXT_FIELDS:entry['result_kind']='text_search' if level=='snippet' else 'text_content'
    if command=='nmrdata-institution-spectrum':level='spectrum_table';entry['result_kind']='spectrum_table'
    if command=='hbn-institution-values':entry['result_kind']='observations';level='observations'
    if command in {'drcnet-ip-search','hbn-institution-indicators','htcases-institution-catalog'}:entry['result_kind']='catalog'
    if command in {'rdfybk-institution-catalog','dingxiu-institution-catalog','tianlu-ip-catalog','nmrdata-institution-catalog'}:entry['result_kind']='bibliographic'
    if command=='infobank-search':entry['result_kind']='text_search'
    if command=='htcases-institution-detail':entry['result_kind']='metadata'
    kind=entry['result_kind']
    if kind!='unclassified':entry['result_kind_basis']='curated adapter-output contract; not live evidence'
    entry['content_level_hint']=level or {'observations':'observations','catalog':'catalog','bibliographic':'bibliographic','metadata':'metadata','text_search':'search_results'}.get(kind,'unclassified')
    entry['content_level_basis']='adapter-output contract; not proof of live availability'
    if command in FOLLOWUPS:
        entry['followup_template']={**FOLLOWUPS[command],'binding':'占位符取自同一条目录记录，保留原始值和完整题名；不得猜号、改写或简繁转换。先help并核验每次详情响应。'}
    return entry

def select(value,path):
    nodes=[value]
    for key in path.split('.'):
        following=[]
        for node in nodes:
            if key=='*':
                if isinstance(node,dict):following.extend(node.values())
                elif isinstance(node,list):following.extend(node)
            elif isinstance(node,dict) and key in node:following.append(node[key])
            elif isinstance(node,list) and key.isdigit() and int(key)<len(node):following.append(node[int(key)])
        nodes=following
    return nodes

def records(value):
    if isinstance(value,list):
        if len(value)==2 and isinstance(value[0],dict) and isinstance(value[1],list):return value[1]
        return value
    if isinstance(value,dict):
        for key in ('items','rows','records','value','data','results','result','dataflows','candidates','observations','indicators','economies','dataset','Dataset','idlist'):
            if isinstance(value.get(key),list):return value[key]
        for key in ('result','data','message','resultList','response','esearchresult'):
            if isinstance(value.get(key),dict):
                child=records(value[key])
                if child is not None:return child
    return None

def numeric(value):
    if value is None or isinstance(value,bool):return False
    try:return math.isfinite(float(str(value).replace(',','')))
    except (ValueError,TypeError):return False

def assess(command,kind,value,execution_ok=True):
    rows=records(value);count=len(rows) if rows is not None else None
    out={'execution_ok':bool(execution_ok),'record_count':count,'has_records':bool(count) if count is not None else None,'has_content':False,'content_level':{'catalog':'catalog','bibliographic':'bibliographic','metadata':'metadata','text_search':'search_results','observations':'observations'}.get(kind,kind),'has_data':None,'numeric_observation_count':None,'data_verified':False}
    if not execution_ok:return {**out,'result_status':'error','has_data':False}
    if command in TEXT_FIELDS:
        level,paths=TEXT_FIELDS[command]
        from bs4 import BeautifulSoup
        parts=[BeautifulSoup(v,'html.parser').get_text(' ',strip=True) for path in paths for v in select(value,path) if isinstance(v,str) and v.strip()]
        chars=sum(len(x) for x in parts)
        body=chars>0 and level!='snippet'
        return {**out,'content_level':level,'has_records':bool(chars),'has_content':body,'has_data':body,'result_status':('snippet' if level=='snippet' else 'content') if chars else 'empty_result','text_characters':chars,'scope_note':'只验证当前一篇/一页/阅读器片段；短命中片段不等于正文，不代表整本或整库全文、影像及下载权限。'}
    if command=='nmrdata-institution-spectrum':
        found=bool(rows)
        return {**out,'content_level':'spectrum_table','has_records':found,'has_content':found,'has_data':found,'result_status':'content' if found else 'empty_result','scope_note':'仅当前记录的碳核磁表；不是谱图或化学结构鉴定，单位按源站说明。'}
    if kind=='observations':
        paths=MEASURES.get(command)
        if command=='nasa-power-daily' and isinstance(value,dict):
            paths=['rows.*.'+key for key in value.get('parameters',{}) if isinstance(key,str) and key and all(c.isupper() or c.isdigit() or c=='_' for c in key)] or None
        if command=='hbn-institution-values':
            code=str(value.get('indicator_code','')) if isinstance(value,dict) else ''
            fields=[x.get('field') for x in value.get('columns',[]) if isinstance(x,dict) and x.get('field')=='hbn_0_'+code] if code else []
            paths=['rows.*.'+field for field in fields] or None
        if not paths:return {**out,'result_status':'observations_unverified','data_note':'此命令尚未声明可核验的测量字段；不能从ID、年份或行数推定取到数值。'}
        values=[v for path in paths for v in select(value,path)]
        if command=='nasa-power-daily':values=[None if v in (-999,-999.0,'-999') else v for v in values]
        found=sum(numeric(v) for v in values)
        out.update(numeric_observation_count=found,missing_measure_count=len(values)-found,has_data=found>0,has_content=found>0,data_verified=found>0,measure_paths=paths)
        if found:return {**out,'has_records':True,'result_status':'observations'}
        if count==0:return {**out,'result_status':'empty_result','empty_reason':'no_matching_observations','data_note':'查询条件下没有观测行；不推断整个数据库没有数据。'}
        return {**out,'result_status':'missing_observations','empty_reason':'matching_rows_without_numeric_measures','data_note':'有时期或记录响应，但没有可核验数值；缺失、抑制或空值不补零。'}
    if rows is not None:
        return {**out,'has_data':False,'result_status':kind if count else 'empty_result','data_note':'仅返回目录、题录或检索记录，不等于正文、影像、谱图或数值。',**({'empty_reason':'no_match','data_note':'请求完成但当前过滤条件零命中；不等于取得数值或源站无数据。'} if not count else {})}
    if kind=='metadata':return {**out,'has_data':False,'has_records':bool(value),'result_status':'metadata' if value else 'empty_result'}
    return {**out,'result_status':'unclassified','data_note':'返回结构尚未完成类型与测量字段核验，不把请求成功称为已取得数值。'}
