"""CALIS e读公开跨库题录分页检索，不请求全文或文献传递。"""
import release_runtime
import json, time
import requests
URL = 'https://yidu.calis.edu.cn/prod-api/yidu/resource/query'
_last_request = 0.0

def calis_yidu_api_search(keyword, page=1, page_size=10, *, resource_type='all'):
    global _last_request
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('关键词须为1–100字')
    categories = {'all': '0', 'book': '28', 'journal_article': '10', 'thesis': '2', 'newspaper': 'ct-scm-000002', 'yearbook_entry': 'ct-scm-000001', 'reference_entry': 'ct-scm-000000'}
    if resource_type not in categories:
        raise ValueError('类型须为 all、book、journal_article、thesis、newspaper、yearbook_entry 或 reference_entry')
    if not isinstance(page, int) or not isinstance(page_size, int) or page < 1 or (not 1 <= page_size <= 10) or (page * page_size > 2000):
        raise ValueError('每页1至10条，页码范围不得超过前2000条')
    q = keyword.strip()
    category = categories[resource_type]
    c = {'all4reader': {'type': 'all4reader', 'label': q, 'value': q, 'title': '全部', 'andor': '0', 'relation': '0', 'category': category}}
    p = {'offset': page, 'limit': page_size, 'sort': None, 'exp': [{'field': 'all4reader', 'value': q, 'label': q, 'relation': '0', 'op': '0', 'resource': category, 'typeNew': category + '-1'}], 'facet': [], 'searchJson': json.dumps({'condition': c, 'secondCondition': [], 'searchType': 'simple'}, ensure_ascii=False), 'refresh': ''}
    delay = 1 - (time.monotonic() - _last_request)
    if delay > 0:
        time.sleep(delay)
    _last_request = time.monotonic()
    r = requests.post(URL, json=p, timeout=20)
    r.raise_for_status()
    out = r.json()
    if out.get('code') != 200 or not isinstance(out.get('data'), dict):
        raise ValueError('CALIS 查询未成功，可能需要验证或登录')
    d = out['data']
    hits = d.get('content')
    total = d.get('total')
    if not isinstance(hits, list) or not isinstance(total, int):
        raise ValueError('未识别题录或总数')
    items = []
    for x in hits:
        if not x.get('ukey') or not x.get('string_title'):
            raise ValueError('题名或记录编号缺失')
        items.append({'id': x['ukey'], 'title': x['string_title'], 'type': x.get('schemacode'), 'author': x.get('string_creator'), 'journal': x.get('string_journal_title'), 'year': x.get('string_publishyear'), 'publisher': x.get('string_publisher'), 'citation': x.get('quote')})
    return {'source': 'CALIS e读跨库公开题录', 'source_url': 'https://yidu.calis.edu.cn/', 'keyword': q, 'resource_type': resource_type, 'total': total, 'max_results': d.get('maxTotal'), 'page': page, 'items': items, 'note': '跨库发现题录；查询范围与可获取结果上限以平台为准，未确认机构身份、持有或全文权限。'}
