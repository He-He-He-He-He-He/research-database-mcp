"""UNHCR Refugee Statistics API demographic records (one page)."""
import release_runtime
import re
import requests
from unhcr_population_adapter import _resolve
URL = 'https://api.unhcr.org/population/v1/demographics/'

def demographics(year, origin, asylum=None, page=1, limit=20, code_system='unhcr'):
    if isinstance(year, bool) or not isinstance(year, int) or (not 1950 <= year <= 2100):
        raise ValueError('invalid year')
    if not isinstance(origin, str) or not re.fullmatch('[A-Z]{3}', origin):
        raise ValueError('origin must be a three-letter UNHCR code')
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
    response = requests.get(URL, params=params, timeout=35)
    response.raise_for_status()
    result = response.json()
    if not isinstance(result, dict) or not isinstance(result.get('items'), list) or result.get('page') != page:
        raise ValueError('unexpected UNHCR response')
    if any((item.get('coo') != origin_code or item.get('year') != year or (asylum_code and item.get('coa') != asylum_code) for item in result['items'])):
        raise ValueError('UNHCR returned rows outside requested dimensions')
    return {**result, 'toolkit_source_url': response.url, 'toolkit_note': 'Demographic reporting coverage varies. Preserve source strings and missing symbols; zero, missing and unreported are distinct. Pagination may change when source data updates.'}
