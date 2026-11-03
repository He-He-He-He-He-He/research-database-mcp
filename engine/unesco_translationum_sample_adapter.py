"""UNESCO Index Translationum DataHub sample, NOT complete catalogue."""
import release_runtime
import re
import requests
BASE = 'https://data.unesco.org/api/explore/v2.1/catalog/datasets/tran001'
PAGE = 'https://data.unesco.org/explore/assets/tran001/'

def _get(path='', params=None):
    r = requests.get(BASE + path, params=params, timeout=35)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, dict):
        raise ValueError('unexpected response')
    return j

def search(country, keyword='', limit=20, offset=0):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{2}', country):
        raise ValueError('country must be two-letter code')
    if not isinstance(keyword, str) or len(keyword) > 120 or any((c in keyword for c in ('"', '\\', '\n', '\r'))):
        raise ValueError('invalid keyword')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or (not 0 <= offset <= 10000):
        raise ValueError('invalid pagination')
    metadata = _get().get('metas', {}).get('default', {})
    where = f'iso2 = "{country}"' + (f' AND search(original_title,"{keyword}")' if keyword else '')
    params = {'where': where, 'limit': limit, 'offset': offset}
    data = _get('/records', params)
    if not isinstance(data.get('total_count'), int) or not isinstance(data.get('results'), list):
        raise ValueError('unexpected records')
    if any((not isinstance(r, dict) or r.get('iso2') != country for r in data['results'])):
        raise ValueError('out-of-filter result')
    return {'source': BASE + '/records', 'page': PAGE, 'request': params, 'data_modified': metadata.get('data_processed'), 'license': metadata.get('license'), 'total': data['total_count'], 'offset': offset, 'rows': data['results'], 'note': 'UNESCO DataHub describes these historical 1978–2008 entries as a sample, not complete Index Translationum or all translations. Country is publication country; records may group several translations. Preserve translations field as the source string. Search uses source text matching, not guaranteed exact title. Dataset CC BY-SA 4.0; underlying bibliographic content may have separate rights.'}
