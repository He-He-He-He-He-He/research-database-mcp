"""The Metropolitan Museum of Art Collection API v1.1 search and object detail."""
import release_runtime
import requests
BASE = 'https://collectionapi.metmuseum.org/public/collection'
DOC = 'https://metmuseum.github.io/'

def _get(path, params=None):
    r = requests.get(BASE + path, params=params, timeout=30)
    r.raise_for_status()
    if len(r.content) > 3000000:
        raise ValueError('Unexpected response size')
    return (r.url, r.json())

def search(keyword, limit=10, offset=0):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('keyword must be 1–100 characters')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('limit must be 1–100')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 0 <= offset <= 1000000):
        raise ValueError('offset out of range')
    url, data = _get('/v1.1/search', {'q': keyword.strip(), 'limit': limit, 'offset': offset})
    ids = data.get('objectIDs')
    ids = [] if ids is None and data.get('total') == 0 else ids
    if not isinstance(data.get('total'), int) or not isinstance(ids, list) or any((isinstance(x, bool) or not isinstance(x, int) for x in ids)):
        raise ValueError('Unexpected search response')
    return {'source_url': url, 'documentation': DOC, 'total': data['total'], 'offset': offset, 'limit': limit, 'object_ids': ids, 'note': 'Search returns IDs only; retrieve object detail separately. Search metadata and images have distinct rights.'}

def object_detail(object_id):
    if isinstance(object_id, bool) or not isinstance(object_id, int) or (not 1 <= object_id <= 999999999):
        raise ValueError('object_id must be a positive integer')
    url, data = _get('/v1/objects/' + str(object_id))
    if not isinstance(data, dict) or data.get('objectID') != object_id:
        raise ValueError('Unexpected object response')
    return {'source_url': url, 'documentation': DOC, 'data': data, 'note': 'Met open-access metadata; check isPublicDomain and the object page before image reuse. Object and rights status can change.'}
