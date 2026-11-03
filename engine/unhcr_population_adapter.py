"""UNHCR official refugee statistics population records."""
import release_runtime
import re
import requests
from functools import lru_cache
URL = 'https://api.unhcr.org/population/v1/population/'
COUNTRIES_URL = 'https://api.unhcr.org/population/v1/countries/'

@lru_cache(maxsize=1)
def _countries():
    response = requests.get(COUNTRIES_URL, params={'limit': 1000}, timeout=35)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict) or data.get('maxPages') != 1 or (not isinstance(data.get('items'), list)):
        raise ValueError('UNHCR country directory is incomplete or has changed')
    return tuple(data['items'])

def _resolve(code, code_system):
    field = 'iso' if code_system == 'iso3' else 'code'
    found = {x.get('code') for x in _countries() if x.get(field) == code and x.get('code')}
    if len(found) != 1:
        raise ValueError('unknown or ambiguous ' + code_system + ' country code: ' + code)
    return next(iter(found))

def population(year, origin, asylum=None, page=1, limit=20, code_system='unhcr'):
    if isinstance(year, bool) or not isinstance(year, int) or (not 1950 <= year <= 2100):
        raise ValueError('invalid year')
    if not isinstance(origin, str) or not re.fullmatch('[A-Z]{3}', origin):
        raise ValueError('invalid origin code')
    if asylum is not None and (not isinstance(asylum, str) or not re.fullmatch('[A-Z]{3}', asylum)):
        raise ValueError('invalid asylum code')
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise ValueError('invalid page')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('invalid limit')
    if code_system not in ('unhcr', 'iso3'):
        raise ValueError('code_system must be unhcr or iso3')
    origin_code = _resolve(origin, code_system)
    asylum_code = _resolve(asylum, code_system) if asylum else None
    params = {'year': year, 'coo': origin_code, 'page': page, 'limit': limit}
    if asylum_code:
        params['coa'] = asylum_code
    else:
        params['coa_all'] = 'true'
    r = requests.get(URL, params=params, timeout=35)
    r.raise_for_status()
    d = r.json()
    if not isinstance(d, dict) or not isinstance(d.get('items'), list) or d.get('page') != page:
        raise ValueError('unexpected UNHCR response')
    if any((item.get('coo') != origin_code or item.get('year') != year or (asylum_code and item.get('coa') != asylum_code) for item in d['items'])):
        raise ValueError('UNHCR returned rows outside requested dimensions')
    return {**d, 'toolkit_source_url': r.url, 'toolkit_note': 'Population stock categories are not applications or durable solutions. Preserve source zeros and missing symbols; categories and reporting coverage may overlap. Page contents may change when the source updates.'}
