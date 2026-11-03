"""ASTM International public Crossref DOI metadata, not licensed full text."""
import release_runtime
import requests
from crossref_catalog_validation import validate_crossref_page
BASE = 'https://api.crossref.org/members/381/works'

def search(query, kind='standard', rows=10, offset=0):
    if not isinstance(query, str) or not query.strip() or len(query) > 300:
        raise ValueError('请输入 1–300 字符检索词')
    if kind not in ('standard', 'journal-article', 'book-chapter'):
        raise ValueError('类型限 standard、journal-article、book-chapter')
    if any((isinstance(v, bool) or not (isinstance(v, int) or (isinstance(v, str) and v.isascii() and v.isdigit())) for v in (rows, offset))):
        raise ValueError('rows 与 offset 须为整数')
    if not 1 <= int(rows) <= 100 or not 0 <= int(offset) <= 9000:
        raise ValueError('rows 1–100；offset 0–9000')
    r = requests.get(BASE, params={'filter': 'type:' + kind, 'query.bibliographic': query, 'rows': int(rows), 'offset': int(offset)}, timeout=30)
    r.raise_for_status()
    m = r.json().get('message')
    validate_crossref_page(m, int(rows))
    items = []
    for x in m['items']:
        items.append({'title': (x.get('title') or [''])[0], 'doi': x.get('DOI'), 'url': x.get('URL'), 'type': x.get('type'), 'publisher': x.get('publisher'), 'published': x.get('published', {}).get('date-parts'), 'authors': x.get('author', []), 'container_title': x.get('container-title', [])})
    return {'source': 'Crossref 成员 381 ASTM International', 'query': query, 'kind': kind, 'provider_total': m.get('total-results'), 'offset': int(offset), 'items': items, 'note': '公开题录，版本可能历史或撤销；不证明完整、现行、浙大订购或全文权限。'}
