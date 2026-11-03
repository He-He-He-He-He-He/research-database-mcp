"""IOP Publishing book metadata from Crossref; not a library entitlement check."""
import release_runtime
import requests
BASE = 'https://api.crossref.org/members/266/works'

def search(query, kind='monograph', rows=10, offset=0):
    if kind not in ('monograph', 'book-chapter'):
        raise ValueError('kind 限 monograph 或 book-chapter')
    if not query.strip():
        raise ValueError('请输入检索词')
    if not 1 <= int(rows) <= 100 or int(offset) < 0 or int(offset) > 9000:
        raise ValueError('rows 1–100，offset 0–9000')
    r = requests.get(BASE, params={'filter': 'type:' + kind, 'query.title': query, 'rows': int(rows), 'offset': int(offset)}, timeout=25)
    r.raise_for_status()
    m = r.json()['message']
    results = []
    for x in m['items']:
        results.append({'title': (x.get('title') or [''])[0], 'doi': x.get('DOI'), 'url': x.get('URL'), 'type': x.get('type'), 'publisher': x.get('publisher'), 'published': x.get('published', {}).get('date-parts'), 'authors': x.get('author', []), 'isbn': x.get('ISBN', []), 'container_title': x.get('container-title', [])})
    return {'source': 'Crossref member 266: IOP Publishing', 'kind': kind, 'query': query, 'total_results': m['total-results'], 'offset': int(offset), 'items': results, 'note': '公开 DOI 题录，不证明浙大馆藏订购、全文权限或覆盖全部 IOP 图书。'}
