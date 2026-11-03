"""UNESCO DataHub World Heritage List public records API."""
import release_runtime
import requests
BASE = 'https://data.unesco.org/api/explore/v2.1/catalog/datasets/whc001'
PAGE = 'https://data.unesco.org/explore/dataset/whc001/'

def _get(path='', params=None):
    r = requests.get(BASE + path, params=params, timeout=35)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, dict):
        raise ValueError('unexpected response')
    return j

def search(country, limit=20, offset=0):
    if not isinstance(country, str) or not country.strip() or len(country) > 120 or any((c in country for c in ('"', '\\', '\n', '\r'))):
        raise ValueError('invalid country')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or (not 0 <= offset <= 10000):
        raise ValueError('invalid pagination')
    metadata = _get()
    meta = metadata.get('metas', {}).get('default', {})
    params = {'where': f'states_names = "{country}"', 'limit': limit, 'offset': offset}
    data = _get('/records', params)
    if not isinstance(data.get('total_count'), int) or not isinstance(data.get('results'), list):
        raise ValueError('unexpected records')
    if any((not isinstance(r, dict) or country.casefold() not in [str(x).casefold() for x in r.get('states_names', [])] for r in data['results'])):
        raise ValueError('out-of-filter result')
    return {'source': BASE + '/records', 'page': PAGE, 'request': params, 'data_modified': meta.get('data_processed'), 'metadata_modified': meta.get('metadata_processed'), 'license': meta.get('license'), 'total': data['total_count'], 'offset': offset, 'rows': data['results'], 'note': 'Inscribed World Heritage properties, not all heritage sites or national monuments. Transboundary properties can belong to multiple states and should not be summed across countries. Preserve inscription date, categories, boundaries and danger status as published. Dataset states CC BY-SA 4.0; individual media rights may differ.'}
