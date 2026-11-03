"""CALIS 外文期刊网公开刊名目录及单刊题录。"""
import release_runtime
import json
import re
import requests
from calis_foreign_journals_api_adapter import BAD, _id
BASE = 'https://ccc2.calis.edu.cn/prod-api/ccc/journal/'
FIELDS = {'issn': 'issn_raw', 'publisher': 'publisher_raw', 'openaccess': 'open_access_raw', 'isoa': 'isoa_raw'}

def _item(x):
    if not isinstance(x, dict) or not _id(x.get('id')) or (not isinstance(x.get('journaltitle'), str)) or (not x['journaltitle'].strip()) or BAD.search(x['journaltitle']):
        raise RuntimeError('期刊编号或刊名异常')
    o = {'id': str(x['id']), 'title_raw': x['journaltitle']}
    omitted = []
    for k, name in FIELDS.items():
        v = x.get(k)
        if v is None:
            o[name] = None
        elif isinstance(v, str) and len(v) <= 20000 and (not BAD.search(v)):
            o[name] = v
        elif type(v) in (int, float, bool):
            o[name] = v
        else:
            o[name] = None
            omitted.append(k)
    o['source_fields_omitted'] = omitted
    return o

def search(keyword, page=1, limit=10, session=None):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 200 or re.search('[\\x00-\\x1f]', keyword):
        raise ValueError('刊名须为 1–200 字单行文本')
    if type(page) is not int or type(limit) is not int or page < 1 or (not 1 <= limit <= 10) or (page * limit > 2000):
        raise ValueError('每页 1–10 条，最多请求前 2000 项')
    q = keyword.strip()
    v = {'list': [{'type': 'journaltitle', 'searchValue': q, 'label': q, 'andor': 'and', 'relation': '2'}], 'nav': {}}
    c = {'condition': {'journaltitle': {'type': 'journaltitle', 'label': q, 'value': q, 'title': '刊名', 'andor': 'and', 'relation': '2'}}}
    body = {'offset': page, 'limit': limit, 'journalTypeStr': '', 'queryValue': json.dumps(v, ensure_ascii=False), 'searchJson': json.dumps(c, ensure_ascii=False)}
    try:
        r = (session or requests.Session()).post(BASE + 'ccc/ordinary/query', json=body, timeout=30, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('期刊目录不可用')
        j = r.json()
        d = j.get('data') if isinstance(j, dict) and j.get('code') == 200 else None
        if not isinstance(d, dict) or type(d.get('total')) is not int or d['total'] < 0 or (type(d.get('maxTotal')) is not int) or (d['maxTotal'] < 0) or (not isinstance(d.get('content'), list)):
            raise RuntimeError('期刊总数或结构异常')
        n = min(limit, max(0, min(d['total'], d['maxTotal']) - (page - 1) * limit))
        if len(d['content']) != n:
            raise RuntimeError('期刊数量与请求页次不一致，数据可能变化')
        return {'source': 'CALIS 外文期刊网公开刊名目录', 'query': q, 'page': page, 'page_size': limit, 'total_raw': d['total'], 'max_total_raw': d['maxTotal'], 'items': [_item(x) for x in d['content']], 'note': '按站方刊名包含模式检索；条件和页码未回显，排序及总数可能变化，连续分页须保持页长。最多访问站方上限；机构身份、期刊持有及全文权限未验证。原始开放标记含义须核对。'}
    except (requests.RequestException, ValueError):
        raise RuntimeError('期刊检索连接失败或响应无法解析') from None

def detail(journal_id, expected_title, session=None):
    if not _id(journal_id):
        raise ValueError('期刊编号须来自检索结果')
    if not isinstance(expected_title, str) or not expected_title.strip() or len(expected_title) > 2000 or re.search('[\\x00-\\x1f]', expected_title):
        raise ValueError('须提供完整刊名')
    try:
        r = (session or requests.Session()).get(BASE + 'getJournalDetail/ccc/' + str(journal_id), timeout=30, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('期刊详情不可用')
        j = r.json()
        d = j.get('data') if isinstance(j, dict) and j.get('code') == 200 else None
        x = d.get('detailData') if isinstance(d, dict) else None
        item = _item(x)
        if item['id'] != str(journal_id) or item['title_raw'] != expected_title.strip():
            raise RuntimeError('期刊详情编号或刊名不一致')
        return {'source': 'CALIS 外文期刊网公开单刊题录', **item, 'note': '站方编号及刊名与检索结果核对；公开题录不确认浙江大学持有或全文权限，开放标记含义须核对；未请求文献传递。'}
    except (requests.RequestException, ValueError):
        raise RuntimeError('期刊详情连接失败或响应无法解析') from None
