"""RDFYBK school IP topic search catalog without full texts."""
import release_runtime
import datetime
import html
import json
import re
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.rdfybk.com/'

def search(keyword, page=1, limit=5, start_year=1900, end_year=None, session=None, field='topic', match='source-default', second_keyword='', second_field='author', logic='and', second_match='fuzzy'):
    if not isinstance(second_keyword, str) or len(second_keyword) > 100 or any((ord(c) < 32 for c in second_keyword)):
        raise ValueError('第二关键词须为不超过100字的单行文本')
    if second_field not in ('topic', 'title', 'author', 'keywords', 'abstract') or logic not in ('and', 'not') or second_match not in ('exact', 'fuzzy'):
        raise ValueError('第二条件字段或逻辑无效')
    if not second_keyword.strip() and (second_field != 'author' or logic != 'and' or second_match != 'fuzzy'):
        raise ValueError('指定第二条件时须提供关键词')
    fields = {'topic': ('0', '主题词'), 'title': ('1', '标题'), 'author': ('2', '作者'), 'keywords': ('3', '关键词'), 'abstract': ('5', '内容摘要')}
    modes = {'source-default': None, 'exact': '1', 'fuzzy': '2'}
    if field not in fields or match not in modes:
        raise ValueError('检索字段或匹配模式无效')
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100:
        raise ValueError('关键词须为 1–100 字')
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('页码须为正整数')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 20):
        raise ValueError('每页最多 20 条')
    if end_year is None:
        end_year = datetime.date.today().year
    if any((type(x) is not int or x < 1000 or x > 9999 for x in (start_year, end_year))) or start_year > end_year:
        raise ValueError('年份范围无效')
    q = keyword.strip()
    s = session or requests.Session()
    r = s.get(BASE, timeout=20)
    r.raise_for_status()
    p = BeautifulSoup(r.content, 'html.parser')
    text = p.get_text(' ', strip=True)
    if not re.search('浙江大学\\s+退出', text):
        raise RuntimeError('未确认浙江大学机构会话')
    body = {'TreeCode': '', 'StartYear': str(start_year), 'EndYear': str(end_year), 'Order': '', 'PageSize': limit, 'PageIndex': page, 'IsBuy': 0, 'ListSearchCondition': [{'Type': '0', 'KeyWord': q, 'RelationShip': '1'}]}
    body['ListSearchCondition'][0]['Type'] = fields[field][0]
    if modes[match] is not None:
        body['ListSearchCondition'][0]['IsAccurate'] = modes[match]
    if second_keyword.strip():
        body['ListSearchCondition'].append({'Type': fields[second_field][0], 'KeyWord': second_keyword.strip(), 'IsAccurate': modes[second_match], 'RelationShip': '1' if logic == 'and' else '3'})
    r = s.post(BASE + 'Qw/MutilSearchTow', data={'data': json.dumps(body, ensure_ascii=False), 'syfl': 'QwWzBk'}, timeout=20)
    r.raise_for_status()
    j = r.json()
    raw = (j.get('Count') or {}).get('RecordCount') if isinstance(j, dict) and isinstance(j.get('Count'), dict) else None
    if not (type(raw) is int or (isinstance(raw, str) and raw.isdigit())) or int(raw) < 0 or (not isinstance(j.get('ListArticle'), list)) or (len(j['ListArticle']) > limit):
        raise RuntimeError('题录响应异常')
    expected = min(limit, max(0, int(raw) - (page - 1) * limit))
    if len(j['ListArticle']) != expected:
        raise RuntimeError('站方返回条数与总数及页码不一致，可能数据变化或响应不完整')
    items = []
    for x in j['ListArticle']:
        if not isinstance(x, dict) or not isinstance(x.get('Id'), str) or (not isinstance(x.get('Title'), str)):
            raise RuntimeError('题录编号或标题缺失')
        item = {'id': x['Id'], 'title': x['Title'].strip(), 'authors': x.get('Author') or None, 'journal': x.get('PdcName') or None, 'year': x.get('PdcYear'), 'source_OrgPdcYear_raw': x.get('OrgPdcYear'), 'issue': x.get('PdcNo'), 'original_journal': x.get('OrgName') or None, 'source_type': x.get('DbCode')}
        omitted = []
        for key in ('ClassName', 'PdcCode', 'OrgAddr'):
            value = x.get(key)
            if value is not None and (not isinstance(value, str) or re.search('[a-z][a-z0-9+.-]*://|www\\.|(?:href|src)\\s*=|(?:token|session|sid|apikey|api_key)\\s*=', html.unescape(value), re.I)):
                item['source_' + key + '_raw'] = None
                omitted.append(key)
            else:
                item['source_' + key + '_raw'] = value
        if omitted:
            item['source_fields_omitted'] = omitted
        items.append(item)
    result = {'source': '人大复印报刊资料', 'institution': '浙江大学', 'query': q, 'search_field': '主题词', 'start_year': start_year, 'end_year': end_year, 'page': page, 'page_size': limit, 'total': int(raw), 'items': items[:limit], 'note': '跨库主题词题录查询，未筛选已购内容；上游可能分词而返回低相关结果；保留上游数据库类型，全文及转载关系须另核。'}
    if field != 'topic' or match != 'source-default':
        result['search_field'] = fields[field][1]
        result['match_requested'] = match
        result['note'] = '按站方高级检索字段和匹配模式请求；响应未回显字段和页码，精确/模糊为站方术语，模糊可能分词，不保证字面匹配。未筛选已购内容，全文及转载关系须另核。'
    if second_keyword.strip():
        result['second_condition'] = {'keyword': second_keyword.strip(), 'field': fields[second_field][1], 'match_requested': second_match, 'logic_requested': logic}
        result['note'] += ' 第二条件同样由站方执行；标题+作者、作者+标题、标题+关键词样本已验证，其他组合须核对；站方“或者”关系出现异常，暂未提供。'
    result['note'] += ' year 与 source_OrgPdcYear_raw 均为站方原值，样本可能不同；字段含义和时间顺序须核对原文。 source_ClassName_raw、source_PdcCode_raw、source_OrgAddr_raw 为搜索响应原字段，含义未确认；含链接、疑似凭据或异常结构时省略并标记。'
    return result
