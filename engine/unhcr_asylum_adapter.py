"""UNHCR official asylum application and decision records, paged."""
import release_runtime
import re
import requests
from unhcr_population_adapter import _resolve
BASE = 'https://api.unhcr.org/population/v1/'

def query(kind, year, origin, asylum=None, page=1, limit=20, code_system='unhcr'):
    paths = {'applications': 'asylum-applications/', 'decisions': 'asylum-decisions/'}
    if kind not in paths:
        raise ValueError('kind must be applications or decisions')
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
    response = requests.get(BASE + paths[kind], params=params, timeout=35)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict) or not isinstance(data.get('items'), list) or data.get('page') != page:
        raise ValueError('unexpected UNHCR response')
    if any((item.get('coo') != origin_code or item.get('year') != year or (asylum_code and item.get('coa') != asylum_code) for item in data['items'])):
        raise ValueError('UNHCR returned rows outside requested dimensions')
    return {**data, 'toolkit_source_url': response.url, 'toolkit_note': 'Applications and decisions are distinct events, not refugee population stock; source total is a category aggregate, not a row count. Preserve source zero strings and missing symbols. Pagination may change with updates.'}
