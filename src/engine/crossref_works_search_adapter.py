"""Crossref public works search with bounded offset pagination."""
import release_runtime
import requests
URL = 'https://api.crossref.org/works'
DOC = 'https://www.crossref.org/documentation/retrieve-metadata/rest-api/'

def search(keyword, rows=5, offset=0):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 1000 or any((ord(x) < 32 for x in keyword)):
        raise ValueError('关键词须为 1–1000 个非控制字符')
    if type(rows) is not int or not 1 <= rows <= 20 or type(offset) is not int or (offset < 0) or (offset + rows > 10000):
        raise ValueError('rows 须为 1–20，offset 非负且 offset + rows 不超过 10000')
    p = {'query': keyword.strip(), 'rows': rows, 'offset': offset, 'select': 'DOI,title,author,published,URL,type'}
    try:
        r = requests.get(URL, params=p, timeout=30, headers={'User-Agent': 'ZJUResearchToolkit/1.0 (research metadata)'})
        r.raise_for_status()
        d = r.json()
    except (requests.RequestException, ValueError):
        raise RuntimeError('Crossref 请求失败或返回非 JSON') from None
    m = d.get('message') if isinstance(d, dict) and d.get('status') == 'ok' else None
    if not isinstance(m, dict) or type(m.get('total-results')) is not int or (not isinstance(m.get('items'), list)) or (not isinstance(m.get('query'), dict)):
        raise RuntimeError('Crossref 搜索响应结构异常')
    if m['total-results'] < 0 or m['query'].get('start-index') != offset or len(m['items']) > rows or any((not isinstance(x, dict) or not isinstance(x.get('DOI'), str) for x in m['items'])):
        raise RuntimeError('Crossref 页码或记录结构异常')
    return {**d, 'toolkit_documentation': DOC, 'toolkit_note': 'Crossref 注册元数据不代表全文或机构馆藏。offset 分页最多至前 10000 项；跨请求排序可能变化，页间可能重叠或遗漏，不能假称全集。更深检索须使用官方 cursor 或细化条件。'}
