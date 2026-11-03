"""UNESCO DataHub intangible cultural heritage listing, public records API."""
import release_runtime
import re
import requests
BASE = 'https://data.unesco.org/api/explore/v2.1/catalog/datasets/ich001'
PAGE = 'https://data.unesco.org/explore/dataset/ich001/'

def _get(path='', params=None):
    r = requests.get(BASE + path, params=params, timeout=35)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, dict):
        raise ValueError('unexpected response')
    return j

def search(country, limit=20, offset=0):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{2}', country):
        raise ValueError('country must be two-letter code')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or (not 0 <= offset <= 10000):
        raise ValueError('invalid pagination')
    metadata = _get().get('metas', {}).get('default', {})
    params = {'where': f'countries = "{country}"', 'limit': limit, 'offset': offset}
    data = _get('/records', params)
    if not isinstance(data.get('total_count'), int) or not isinstance(data.get('results'), list):
        raise ValueError('unexpected records')
    if any((not isinstance(r, dict) or country not in r.get('countries', []) for r in data['results'])):
        raise ValueError('out-of-filter result')
    return {'source': BASE + '/records', 'page': PAGE, 'request': params, 'data_modified': metadata.get('data_processed'), 'metadata_modified': metadata.get('metadata_processed'), 'license': metadata.get('license'), 'total': data['total_count'], 'offset': offset, 'rows': data['results'], 'note': 'UNESCO listed intangible cultural heritage elements, not all local practices. Lists include Representative, Urgent Safeguarding and Good Safeguarding Practices; preserve type and inscription year. Multinational inscriptions appear under multiple countries and cannot be summed across them. Dataset CC BY-SA 4.0; individual image/video rights may differ.'}
