"""Crossref 10.1002 前缀的 Wiley 期刊文章公开元数据。"""
import release_runtime
import requests
from crossref_catalog_validation import validate_crossref_page
URL = 'https://api.crossref.org/prefixes/10.1002/works'

def search(query, rows=10, offset=0):
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('关键词须为 1–200 字')
    if isinstance(rows, bool) or not isinstance(rows, int) or (not 1 <= rows <= 50):
        raise ValueError('rows 须为 1–50')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 0 <= offset <= 10000):
        raise ValueError('offset 须为 0–10000')
    if offset + rows > 10000:
        raise ValueError('Crossref works 的 offset + rows 不得超过 10000；此入口未实现 cursor 深分页')
    r = requests.get(URL, params={'query': query.strip(), 'filter': 'type:journal-article', 'rows': rows, 'offset': offset}, timeout=25)
    r.raise_for_status()
    j = r.json()
    m = j.get('message', {})
    if j.get('status') != 'ok':
        raise ValueError('Crossref 响应格式异常')
    validate_crossref_page(m, rows)
    items = []
    for x in m['items']:
        items.append({'title': (x.get('title') or [None])[0], 'doi': x.get('DOI'), 'url': x.get('URL'), 'publisher': x.get('publisher'), 'journal': (x.get('container-title') or [None])[0], 'published': x.get('published', {}).get('date-parts'), 'type': x.get('type')})
    return {'source': 'Crossref 前缀 10.1002 的期刊文章元数据', 'source_url': URL, 'query': query.strip(), 'upstream_total': m['total-results'], 'offset': offset, 'items': items, 'note': '此 DOI 前缀包含 Wiley 登记的文章，但并非 Wiley 全部期刊；出版者以各条记录为准。公开题录不代表浙大馆藏范围或全文权限。'}
