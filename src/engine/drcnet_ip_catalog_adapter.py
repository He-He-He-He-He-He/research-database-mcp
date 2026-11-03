"""国研网教育版校园 IP 登录与单页题名检索，仅返回题录。"""
import release_runtime
import json
import re
from datetime import date
import requests
AUTH = 'https://user.drcnet.com.cn/userapi/loginController/initLoginP'
SEARCH = 'https://search.drcnet.com.cn/search/getSearchString/'

def detail_reference(item):
    code=str(item.get('code') or '')
    match=re.fullmatch(r'[A-Za-z0-9]+_([0-9]{1,12})',code)
    leaves=re.split(r'[|,\s]+',str(item.get('leafIds') or ''))
    paths=[p.split('_') for p in re.split(r'[|\s]+',str(item.get('chnidPath') or ''))]
    candidates=[p for p in paths if len(p)>1 and p[-1] in leaves and all(re.fullmatch(r'[0-9]{1,12}',x) for x in p)]
    if not match or not candidates or not isinstance(item.get('title'),str):return None
    path=candidates[0]
    return {'doc_id':match[1],'leaf_id':path[-1],'channel_id':path[-2],'expected_title':item['title']}

def search(keyword, page=1, limit=5, field='title', start_date=None, end_date=None, source=''):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100 or any((c in keyword for c in '\r\n')):
        raise ValueError('关键词须为1–100字单行文本')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 100):
        raise ValueError('页码须为1–100')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 10):
        raise ValueError('每页条数须为1–10')
    fields = {'fulltext': '0', 'title': '1', 'author': '2', 'keywords': '3', 'source': '4'}
    if field not in fields:
        raise ValueError('field 须为 fulltext、title、author、keywords 或 source')
    if not isinstance(source, str) or len(source) > 100 or any((ord(c) < 32 for c in source)):
        raise ValueError('来源须为不超过100字的单行文本')
    source = source.strip()
    if source and (field != 'title' or start_date is not None or end_date is not None):
        raise ValueError('来源组合仅验证题名且不叠加日期')
    if (start_date is None) != (end_date is None):
        raise ValueError('开始和结束日期须同时提供')
    if start_date is not None:
        try:
            if not isinstance(start_date, str) or not isinstance(end_date, str):
                raise ValueError()
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)
            if start.isoformat() != start_date or end.isoformat() != end_date or start > end:
                raise ValueError()
        except ValueError:
            raise ValueError('日期须为有效且顺序正确的 YYYY-MM-DD') from None
    query = keyword.strip()
    payload = {'attrIndex': '', 'curpage': page, 'pagesize': limit, 'classification1': None, 'classification2': None, 'catalogName': '', 'lisQuery': [{'queryBoolType': 1, 'queryOperator': 2, 'queryItem': fields[field], 'queryString': query}], 'startTime': start_date or '', 'endTime': end_date or '', 'rootlm': '20548', 'resultType': 0, 'lisLeafidCase': [], 'lisLeafid': [], 'chnId': 0, 'sortOrder': 'desc', 'sortField': 'deliveddate'}
    if source:
        payload['lisQuery'].append({'queryBoolType': 1, 'queryOperator': 2, 'queryItem': '4', 'queryString': source})
    with requests.Session() as session:
        r = session.get(AUTH, params={'flag': 'initp'}, timeout=20)
        r.raise_for_status()
        raw = r.text.strip()
        if raw.startswith('(') and raw.endswith(')'):
            raw = raw[1:-1]
        try:
            auth = json.loads(raw)
        except ValueError:
            raise RuntimeError('未识别学校登录响应') from None
        if auth.get('UserName') != '浙江大学图书馆' or auth.get('IsAdvIP') is not True or auth.get('Logined') != 1:
            raise RuntimeError('未确认浙江大学图书馆校园 IP 授权')
        r = session.post(SEARCH, json=payload, timeout=30)
        r.raise_for_status()
        try:
            body = r.json()
        except ValueError:
            raise RuntimeError('国研网检索未返回 JSON') from None
    try:
        data = body['hits']
        total = data['total']
        hits = data['hits']
        if body.get('timed_out') is not False or not isinstance(total.get('value'), int) or total.get('relation') not in ('eq', 'gte') or (not isinstance(hits, list)) or (len(hits) > limit):
            raise ValueError()
        items = []
        for hit in hits:
            x = hit['_source']
            if not isinstance(x.get('title'), str) or not x.get('code'):
                raise ValueError()
            items.append({k: x.get(k) for k in ('code', 'title', 'author', 'source', 'deliveddate', 'leafIds', 'chnidPath')})
    except (KeyError, TypeError, ValueError):
        raise RuntimeError('国研网检索响应结构异常或查询超时') from None
    for item in items:item['detail_reference']=detail_reference(item)
    result = {'source': '国研网教育版', 'institution': '浙江大学图书馆（校园 IP）', 'query': query, 'field': '题名', 'page': page, 'page_size': limit, 'total': total['value'], 'total_relation': total['relation'], 'items': items, 'note': '仅标题检索的单页题录，按站方投递日期降序；原始数值、正文和下载未读取。机构身份不保证每篇全文权限。'}
    if field != 'title':
        result['field'] = field
        result['note'] = '按站方字段查询的单页题录，可能分词匹配，源站未回显字段或页码；全文检索不返回正文，机构身份不保证每篇全文权限。'
    if start_date is not None:
        result['date_filter_requested'] = {'start': start_date, 'end': end_date}
        result['note'] += ' 站方未回显日期条件，样本已验；边界时区和逐条日期须核对。'
    if source:
        result['source_filter_requested'] = source
        result['note'] += ' 题名与来源组合由站方分词，未回显条件，样本显示可能遗漏含查询字的来源，须核对。'
    return result
