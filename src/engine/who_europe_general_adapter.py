"""WHO Europe Data Warehouse official public indicator catalog and data API.

Docs: https://gateway.euro.who.int/en/api/specification/ . Indicator-specific
notes, country notes, units and dimensions are kept with the observations.
"""
import release_runtime
import json
import re
import subprocess
BASE = 'https://dw.euro.who.int/api/v5'
MAX_BYTES = 12000000

def _get(path):
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '35', '--max-filesize', str(MAX_BYTES), BASE + path], capture_output=True, timeout=40)
    if r.returncode:
        raise RuntimeError('WHO Europe request failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > MAX_BYTES:
        raise ValueError('WHO Europe response exceeds 12 MB')
    return json.loads(r.stdout)

def search(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('invalid keyword')
    values = _get('/measures/')
    if not isinstance(values, list):
        raise ValueError('unexpected WHO Europe catalog')
    found = [x for x in values if keyword.casefold() in (str(x.get('code', '')) + ' ' + str(x.get('short_name', '')) + ' ' + str(x.get('full_name', ''))).casefold()]
    return {'source': BASE + '/measures/', 'total': len(values), 'matched': len(found), 'measures': found}

def measure(code, country=None, year=None):
    if not isinstance(code, str) or not re.fullmatch('[A-Za-z0-9_]{1,80}', code):
        raise ValueError('invalid measure code')
    if country is not None and (not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country)):
        raise ValueError('country must be an uppercase WHO Europe country code')
    if year is not None and (isinstance(year, bool) or not isinstance(year, int) or (not 1800 <= year <= 2100)):
        raise ValueError('invalid year')
    path = '/measures/' + code
    obj = _get(path)
    if not isinstance(obj, dict) or obj.get('code') != code or (not isinstance(obj.get('data'), list)):
        raise ValueError('unexpected WHO Europe measure')
    if country is not None:
        obj['data'] = [x for x in obj['data'] if x.get('dimensions', {}).get('COUNTRY') == country]
    if year is not None:
        obj['data'] = [x for x in obj['data'] if x.get('dimensions', {}).get('YEAR') == str(year)]
    return {'source': BASE + path, 'country_filter': country, 'year_filter': year, 'measure': obj, 'note': 'Data filtered locally; notes, definitions, dimensions and metadata remain intact. Coverage and comparability vary by country and year.'}
