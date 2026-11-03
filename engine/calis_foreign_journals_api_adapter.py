"""CALIS 外文期刊网公开文章发现与详情，不请求文献传递或正文。"""
import release_runtime
import json
import re
import requests
BASE = 'https://ccc2.calis.edu.cn/prod-api/ccc/article/ccc/'
BAD = re.compile('[a-z][a-z0-9+.-]*://|www\\.|(?:href|src)\\s*=|(?:token|session|sid|apikey|api_key)\\s*=|<\\s*(?:script|iframe|object|embed|style)\\b|\\bon\\w+\\s*=|[\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f]', re.I)
FIELDS = {'author': 'authors_raw', 'journaltitle': 'journal_raw', 'pyear': 'year_raw', 'volume': 'volume_raw', 'issue': 'issue_raw', 'issn': 'issn_raw', 'eissn': 'eissn_raw', 'doi': 'doi_raw', 'startpage': 'start_page_raw', 'numberofpage': 'page_count_raw', 'publisher': 'publisher_raw', 'keywords': 'keywords_raw', 'abstract': 'abstract_raw'}

def _fields(item):
    out = {}
    omitted = []
    for key, name in FIELDS.items():
        v = item.get(key)
        if v is None:
            out[name] = None
        elif isinstance(v, str) and len(v) <= 20000 and (not BAD.search(v)):
            out[name] = v
        elif type(v) in (int, float):
            out[name] = v
        elif isinstance(v, list) and len(v) <= 1000 and all((isinstance(x, str) and len(x) <= 20000 and (not BAD.search(x)) for x in v)):
            out[name] = v
        else:
            out[name] = None
            omitted.append(key)
    return (out, omitted)

def _id(x):
    return isinstance(x, (str, int)) and (not isinstance(x, bool)) and (re.fullmatch('[1-9][0-9]{0,19}', str(x)) is not None)

def search(keyword, page=1, limit=10, session=None):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 200 or re.search('[\\x00-\\x1f]', keyword):
        raise ValueError('关键词须为 1–200 字单行文本')
    if type(page) is not int or type(limit) is not int or page < 1 or (not 1 <= limit <= 10) or (page * limit > 2000):
        raise ValueError('每页 1–10 条，最多请求前 2000 项')
    q = keyword.strip()
    v = {'list': [{'type': 'all', 'searchValue': q, 'andor': 'and'}], 'secondList': [], 'other': {}, 'nav': {}}
    body = {'offset': page, 'limit': limit, 'sortKey': None, 'queryValue': json.dumps(v, ensure_ascii=False)}
    try:
        r = (session or requests.Session()).post(BASE + 'simple/query', json=body, timeout=30, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('外文期刊检索不可用')
        j = r.json()
        d = j.get('data') if isinstance(j, dict) and j.get('code') == 200 else None
        if not isinstance(d, dict) or type(d.get('total')) is not int or d['total'] < 0 or (type(d.get('maxTotal')) is not int) or (d['maxTotal'] < 0) or (not isinstance(d.get('content'), list)):
            raise RuntimeError('来源总数或结果结构异常')
        n = min(limit, max(0, min(d['total'], d['maxTotal']) - (page - 1) * limit))
        if len(d['content']) != n:
            raise RuntimeError('来源数量与页次不一致，数据可能变化')
        items = []
        for x in d['content']:
            if not isinstance(x, dict) or not _id(x.get('id')) or (not isinstance(x.get('articletitle'), str)) or (not x['articletitle'].strip()) or BAD.search(x['articletitle']):
                raise RuntimeError('题录编号或标题异常')
            f, omitted = _fields(x)
            items.append({'id': str(x['id']), 'title_raw': x['articletitle'], **f, 'source_fields_omitted': omitted})
        return {'source': 'CALIS 外文期刊网公开文章题录', 'query': q, 'page': page, 'page_size': limit, 'total_raw': d['total'], 'max_total_raw': d['maxTotal'], 'items': items, 'note': '站方全面检索可能分词，页码和查询条件不回显；最多返回站方上限内结果，排序及总数可能变化。公开题录未确认浙江大学机构身份或全文权限；不请求文献传递或正文。'}
    except (requests.RequestException, ValueError):
        raise RuntimeError('外文期刊检索连接失败或响应无法解析') from None

def detail(article_id, expected_title, session=None):
    if not _id(article_id):
        raise ValueError('文章编号须来自检索结果')
    if not isinstance(expected_title, str) or not expected_title.strip() or len(expected_title) > 1000 or re.search('[\\x00-\\x1f]', expected_title):
        raise ValueError('须提供检索结果完整标题')
    try:
        r = (session or requests.Session()).get(BASE + 'details', params={'ukey': str(article_id)}, timeout=30, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('外文期刊详情不可用')
        j = r.json()
        data = j.get('data') if isinstance(j, dict) and j.get('code') == 200 else None
        x = data.get('details') if isinstance(data, dict) else None
        if not isinstance(x, dict) or str(x.get('id')) != str(article_id) or x.get('articletitle') != expected_title.strip():
            raise RuntimeError('详情编号或标题与检索结果不一致')
        f, omitted = _fields(x)
        return {'source': 'CALIS 外文期刊网公开文章详情', 'id': str(article_id), 'title_raw': expected_title.strip(), **f, 'source_fields_omitted': omitted, 'note': '站方详情编号和标题与检索结果核对；字段原样保留，缺失不代表不存在。公开元数据未确认学校机构身份或全文权限，未请求正文、原文链接或文献传递。'}
    except (requests.RequestException, ValueError):
        raise RuntimeError('外文期刊详情连接失败或响应无法解析') from None
