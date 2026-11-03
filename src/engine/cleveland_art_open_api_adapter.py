"""Cleveland Museum of Art public collection API: search and artwork detail."""
import release_runtime
import requests
BASE = 'https://openaccess-api.clevelandart.org/api/artworks'
DOC = 'https://www.clevelandart.org/open-access-api'

def _get(path='', params=None):
    r = requests.get(BASE + path, params=params, timeout=30)
    r.raise_for_status()
    if len(r.content) > 5000000:
        raise ValueError('Unexpected response size')
    d = r.json()
    if not isinstance(d, dict):
        raise ValueError('Unexpected response')
    return (r.url, d)

def search(keyword, limit=10, skip=0):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('keyword must be 1–100 characters')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50):
        raise ValueError('limit must be 1–50')
    if isinstance(skip, bool) or not isinstance(skip, int) or (not 0 <= skip <= 1000000):
        raise ValueError('skip out of range')
    url, d = _get('/', {'q': keyword.strip(), 'limit': limit, 'skip': skip})
    if not isinstance(d.get('info', {}).get('total'), int) or not isinstance(d.get('data'), list):
        raise ValueError('Unexpected search response')
    return {'source_url': url, 'documentation': DOC, 'data': d, 'note': 'Search includes artwork metadata; check each record and image licensing status before reuse.'}

def artwork(object_id):
    if isinstance(object_id, bool) or not isinstance(object_id, int) or (not 1 <= object_id <= 999999999):
        raise ValueError('object_id must be a positive integer')
    url, d = _get('/' + str(object_id))
    if not isinstance(d.get('data'), dict) or d['data'].get('id') != object_id:
        raise ValueError('Unexpected artwork response')
    return {'source_url': url, 'documentation': DOC, 'data': d['data'], 'note': 'Metadata and images have different rights; consult share_license_status and the museum object page.'}
