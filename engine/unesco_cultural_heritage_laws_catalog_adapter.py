"""UNESCO DataHub national cultural heritage laws metadata catalogue."""
import release_runtime
import re
import requests
from urllib.parse import urlencode
BASE = 'https://data.unesco.org/api/explore/v2.1/catalog/datasets/mhm001'
PAGE = 'https://data.unesco.org/explore/assets/mhm001/'

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
    if len(data['results']) > limit or (offset < data['total_count'] and (not data['results'])):
        raise ValueError('source page count inconsistent with total')
    if any((not isinstance(r, dict) or country not in (r.get('countries') or []) for r in data['results'])):
        raise ValueError('out-of-filter result')
    return {'source': BASE + '/records', 'source_url': BASE + '/records?' + urlencode(params), 'page': PAGE, 'request': params, 'data_modified': metadata.get('data_processed'), 'license': metadata.get('license'), 'total': data['total_count'], 'offset': offset, 'returned': len(data['results']), 'next_offset': offset + len(data['results']) if data['results'] and offset + len(data['results']) < data['total_count'] else None, 'truncated': offset + len(data['results']) < data['total_count'], 'rows': data['results'], 'note': 'UNESCO cultural heritage laws metadata catalogue, not authoritative law text or proof of current legal force. Missing abrogation/effective dates do not establish status; apparent dates may be year-only defaults. Verify current original legal instrument with competent authorities. Cross-country instruments overlap. Results have no explicit stable sort; source updates can change cross-page ordering. Dataset CC BY-SA 4.0; underlying legal materials may have other terms.'}
