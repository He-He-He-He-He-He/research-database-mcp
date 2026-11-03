"""IEA End-Use Prices public explorer: selected annual price series."""
import release_runtime
import json
import subprocess
from urllib.parse import urlencode
BASE = 'https://api.iea.org/prices'
PAGE = 'https://www.iea.org/data-and-statistics/data-tools/end-use-prices-data-explorer'
LIMIT = 8000000

def _get(path='', params=None):
    url = BASE + path + ('?' + urlencode(params) if params else '')
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '35', '--max-filesize', str(LIMIT), url], capture_output=True, timeout=40)
    if r.returncode:
        raise RuntimeError('IEA request failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > LIMIT:
        raise ValueError('response too large')
    rows = json.loads(r.stdout)
    if not isinstance(rows, list):
        raise ValueError('unexpected response')
    return (url, rows)

def options(dimension, country='', sector=''):
    if dimension not in ('Country', 'CODE_SECTOR', 'CODE_UNIT', 'CODE_PRODUCT', 'CODE_YEAR'):
        raise ValueError('invalid dimension')
    if any((not isinstance(x, str) or len(x) > 120 for x in (country, sector))):
        raise ValueError('invalid filters')
    params = {'CODE_INDICATOR': 'PRICE'}
    if country:
        params['Country'] = country
    if sector:
        params['CODE_SECTOR'] = sector
    url, rows = _get('/list/' + dimension, params)
    return {'source': url, 'page': PAGE, 'dimension': dimension, 'rows': rows}

def prices(country, sector, unit, start, end):
    if any((not isinstance(x, str) or not x.strip() or len(x) > 120 for x in (country, sector, unit))):
        raise ValueError('invalid filter')
    if any((isinstance(x, bool) or not isinstance(x, int) or (not 1900 <= x <= 2100) for x in (start, end))) or start > end:
        raise ValueError('invalid years')
    params = {'Country': country, 'CODE_INDICATOR': 'PRICE', 'CODE_SECTOR': sector, 'CODE_UNIT': unit}
    url, rows = _get('', params)
    if any((not isinstance(r, dict) or any((r.get(k) != v for k, v in params.items())) or (not str(r.get('CODE_YEAR', '')).isdigit()) for r in rows)):
        raise ValueError('unexpected/out-of-filter result')
    return {'source': url, 'page': PAGE, 'page_updated': '2026-05-21', 'year_filter': 'local', 'rows': [r for r in rows if start <= int(r['CODE_YEAR']) <= end], 'note': 'This is the public explorer selection, not the full commercial dataset. Retain original unit, currency basis, year, product and sector; different products and currencies are not directly comparable. Taxes and representativeness depend on source definition. Check methodology; missing data are not zero.'}
