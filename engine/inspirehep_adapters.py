"""INSPIRE-HEP official read-only searches across its research collections."""
import release_runtime
import requests

def search(query, kind='literature', size=10, page=1):
    allowed = {'literature', 'authors', 'institutions', 'conferences', 'seminars', 'journals', 'experiments', 'data'}
    if kind not in allowed:
        raise ValueError('unsupported INSPIRE collection')
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be non-empty')
    if not isinstance(size, int) or isinstance(size, bool) or (not 1 <= size <= 100):
        raise ValueError('size must be between 1 and 100')
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('page must be positive')
    r = requests.get('https://inspirehep.net/api/' + kind, params={'q': query, 'size': size, 'page': page}, timeout=30)
    r.raise_for_status()
    data = r.json()
    hits = data.get('hits')
    if not isinstance(hits, dict) or not isinstance(hits.get('hits'), list):
        raise RuntimeError('Unexpected INSPIRE response')
    return {'source': 'INSPIRE-HEP', 'kind': kind, 'query': query, 'page': page, 'total': hits.get('total'), 'items': hits['hits'], 'note': 'Focused on high-energy physics; record metadata and available links.'}
