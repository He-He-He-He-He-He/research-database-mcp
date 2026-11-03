"""The DHS Program public aggregate survey indicator API.

Official information: https://api.dhsprogram.com/ . Findings are survey estimates
at particular survey years; they are not necessarily annual official statistics.
"""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://api.dhsprogram.com/rest/dhs'
MAX_BYTES = 8000000

def _get(resource, params):
    path = '/' + resource + '?' + urlencode({'f': 'json', **params})
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', str(MAX_BYTES), BASE + path], capture_output=True, timeout=35)
    if r.returncode:
        raise RuntimeError('DHS API request failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > MAX_BYTES:
        raise ValueError('DHS response too large')
    obj = json.loads(r.stdout)
    if not isinstance(obj, dict) or not isinstance(obj.get('Data'), list) or 'TotalPages' not in obj:
        raise ValueError('unexpected DHS response')
    return {'source': BASE + path, 'response': obj}

def _page(page, per_page):
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (page, per_page))) or page < 1 or (not 1 <= per_page <= 100):
        raise ValueError('page must be positive; per_page must be 1 to 100')
    return {'page': page, 'perpage': per_page}

def _code(value, pattern, name):
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        raise ValueError('invalid ' + name)
    return value

def indicators(page=1, per_page=50, indicator=None):
    params = _page(page, per_page)
    if indicator is not None:
        params['indicatorIds'] = _code(indicator, '[A-Za-z0-9_]{1,80}', 'indicator ID')
    return _get('indicators', params)

def countries(page=1, per_page=50):
    return _get('countries', _page(page, per_page))

def data(country, indicator, page=1, per_page=50):
    params = _page(page, per_page)
    params['countryIds'] = _code(country, '[A-Z]{2}', 'DHS country code')
    params['indicatorIds'] = _code(indicator, '[A-Za-z0-9_]{1,80}', 'indicator ID')
    result = _get('data', params)
    for row in result['response']['Data']:
        if row.get('IndicatorId') != indicator or row.get('DHS_CountryCode') != country:
            raise ValueError('DHS returned a row outside requested filters')
    result['note'] = 'Survey-year estimates with breakdowns; inspect characteristic, survey identifier, numerator/denominator and confidence intervals. DHS country codes are not necessarily ISO codes.'
    return result
