"""UNESCO DataHub UNESDOC catalogue title search."""
import release_runtime
import requests
BASE = 'https://data.unesco.org/api/explore/v2.1/catalog/datasets/doc001'
PAGE = 'https://data.unesco.org/explore/assets/doc001/'

def _get(path='', params=None):
    r = requests.get(BASE + path, params=params, timeout=35)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, dict):
        raise ValueError('unexpected response')
    return j

def search(keyword, limit=20, offset=0):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 120 or any((c in keyword for c in ('"', '\\', '\n', '\r'))):
        raise ValueError('invalid title keyword')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or (not 0 <= offset <= 10000):
        raise ValueError('invalid pagination')
    meta = _get().get('metas', {}).get('default', {})
    params = {'where': f'search(title,"{keyword}")', 'limit': limit, 'offset': offset}
    data = _get('/records', params)
    if not isinstance(data.get('total_count'), int) or not isinstance(data.get('results'), list):
        raise ValueError('unexpected records')
    return {'source': BASE + '/records', 'page': PAGE, 'request': params, 'data_modified': meta.get('data_processed'), 'license': meta.get('license'), 'total': data['total_count'], 'offset': offset, 'rows': data['results'], 'note': 'UNESDOC bibliographic records, not full-text retrieval; source title search uses platform matching and may include partial matches. Retain publication year separately from dataset processing time. Catalogue data is CC BY-SA 4.0; each publication and image may have distinct terms and access.'}
