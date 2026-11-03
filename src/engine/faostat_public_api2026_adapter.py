"""FAOSTAT official 2026 API, anonymous guest token, no token persisted."""
import release_runtime
import re
import requests
BASE = 'https://faostatservices.fao.org/api/v1/'
PAGE = 'https://www.fao.org/statistics/highlights-archive/highlights-detail/faostat-launches-a-new-api-developer-portal-to-make-data-access-easier/en'
HEADERS = {'Origin': 'https://www.fao.org', 'Referer': 'https://www.fao.org/faostat/en/', 'User-Agent': 'Mozilla/5.0'}
MAX_BYTES = 8000000

def _code(v, name, pattern):
    if not isinstance(v, str) or not re.fullmatch(pattern, v):
        raise ValueError('invalid ' + name)
    return v

def _get(path, params=None):
    auth = requests.get(BASE + 'auth/guest', headers=HEADERS, timeout=30)
    auth.raise_for_status()
    token = auth.json().get('token')
    if not isinstance(token, str) or not token:
        raise ValueError('guest token unavailable')
    r = requests.get(BASE + path, headers={**HEADERS, 'Authorization': 'Bearer ' + token}, params=params, timeout=40, stream=True)
    r.raise_for_status()
    parts = []
    size = 0
    for part in r.iter_content(65536):
        size += len(part)
        if size > MAX_BYTES:
            raise ValueError('FAOSTAT response too large')
        parts.append(part)
    import json
    value = json.loads(b''.join(parts))
    if not isinstance(value, dict) or not isinstance(value.get('data'), list):
        raise ValueError('unexpected response')
    return value

def dimensions(domain):
    _code(domain, 'domain', '[A-Za-z0-9]{1,12}')
    return {'source': BASE + 'en/dimensions/' + domain + '/', 'api': PAGE, 'response': _get('en/dimensions/' + domain + '/')}

def domains(keyword='', limit=30, *, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 120:
        raise ValueError('invalid keyword')
    if type(limit) is not int or not 1 <= limit <= 100 or type(offset) is not int or (not 0 <= offset <= 100000):
        raise ValueError('invalid limit or offset')
    result = _get('en/groupsanddomains')
    q = keyword.strip().casefold()
    matches = [x for x in result['data'] if isinstance(x, dict) and (not q or any((q in str(x.get(k, '')).casefold() for k in ('group_name', 'group_code', 'domain_name', 'domain_code'))))]
    return {'source': BASE + 'en/groupsanddomains', 'api': PAGE, 'keyword': keyword, 'total_matches': len(matches), 'offset': offset, 'limit': limit, 'rows': matches[offset:offset + limit], 'note': 'The complete source domain list is fetched and filtered locally. Rows can represent groups or subdomains; check domain code and structure before querying. Release dates and revisions can change.'}

def codes(domain, dimension, keyword='', limit=50, *, offset=0):
    _code(domain, 'domain', '[A-Za-z0-9]{1,12}')
    _code(dimension, 'dimension', '[a-zA-Z0-9_]{1,32}')
    if not isinstance(keyword, str) or len(keyword) > 120:
        raise ValueError('invalid keyword')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100) or (type(offset) is not int) or (not 0 <= offset <= 100000):
        raise ValueError('invalid limit or offset')
    path = 'en/codes/' + dimension + '/' + domain + '/'
    result = _get(path)
    matches = [r for r in result['data'] if isinstance(r, dict) and keyword.casefold() in str(r.get('label', '')).casefold()]
    return {'source': BASE + path, 'api': PAGE, 'total_matches': len(matches), 'limit': limit, 'offset': offset, 'next_offset': offset + limit if offset + limit < len(matches) else None, 'truncated': offset + limit < len(matches), 'rows': matches[offset:offset + limit], 'note': 'The complete source code list is fetched again for each request and sliced locally; source ordering may change across requests. Dimension codes are query codes and may differ from codes returned by data endpoint; use FAOSTAT metadata.'}

def data(domain, area, item, element, year):
    _code(domain, 'domain', '[A-Za-z0-9]{1,12}')
    for name, v in [('area', area), ('item', item), ('element', element), ('year', year)]:
        _code(v, name, '[A-Za-z0-9._-]{1,40}')
    params = {'output_type': 'objects', 'area': area, 'item': item, 'element': element, 'year': year}
    result = _get('en/data/' + domain, params)
    return {'source': BASE + 'en/data/' + domain, 'api': PAGE, 'request': params, 'response': result, 'upstream_total_available': False, 'note': 'Official API guest access; units, flags, notes and original metadata retained. Input dimension codes can differ from output codes (e.g. QCL element 2510 returns 5510); check labels and official definitions. Results are same FAOSTAT source as bulk, not independent evidence. The API response does not provide a total count, so completeness is not independently guaranteed. Country and regional totals may overlap.'}
