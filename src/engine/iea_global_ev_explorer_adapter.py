"""IEA Global EV Data Explorer, public explorer API (not the separate bulk product)."""
import release_runtime
import json
import subprocess
from urllib.parse import urlencode
BASE = 'https://api.iea.org/electric-vehicles'
PAGE = 'https://www.iea.org/data-and-statistics/data-tools/global-ev-data-explorer'
DIMENSIONS = {'region', 'parameter', 'category', 'mode', 'powertrain'}
LIMIT = 8000000

def _request(path, params=None):
    url = BASE + path
    if params:
        url += '?' + urlencode(params)
    result = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '35', '--max-filesize', str(LIMIT), url], capture_output=True, timeout=40)
    if result.returncode:
        raise RuntimeError('IEA explorer request failed: ' + result.stderr.decode('utf-8', 'replace')[:500])
    if len(result.stdout) > LIMIT:
        raise ValueError('IEA response too large')
    value = json.loads(result.stdout)
    if not isinstance(value, list):
        raise ValueError('unexpected IEA response')
    return (url, value)

def dimensions(dimension):
    if dimension not in DIMENSIONS:
        raise ValueError('dimension must be region, parameter, category, mode or powertrain')
    source, values = _request('/list/' + dimension)
    if not all((isinstance(x, str) for x in values)):
        raise ValueError('unexpected dimension list')
    return {'source': source, 'explorer': PAGE, 'dimension': dimension, 'values': values}

def data(region, parameter, year, category='Historical', mode=None, powertrain=None):
    if isinstance(year, bool) or not isinstance(year, int) or (not 1900 <= year <= 2100):
        raise ValueError('year must be an integer from 1900 to 2100')
    params = {'region': region, 'parameter': parameter, 'year': year, 'category': category}
    if mode is not None:
        params['mode'] = mode
    if powertrain is not None:
        params['powertrain'] = powertrain
    for key, value in params.items():
        if key != 'year' and (not isinstance(value, str) or not value.strip() or len(value) > 120):
            raise ValueError('invalid ' + key)
    source, rows = _request('', params)
    for row in rows:
        if not isinstance(row, dict) or any((row.get(k) != v for k, v in params.items())):
            raise ValueError('IEA returned data outside requested filters')
    return {'source': source, 'explorer': PAGE, 'explorer_updated': '2026-05-20', 'rows': rows, 'note': 'Preserves original values and units. Historical and projection scenarios differ; EV includes BEV and PHEV, and geographic aggregates overlap individual countries. Do not sum overlapping categories. Explorer page states CC BY 4.0; separate bulk product terms differ. Explorer API is a website endpoint and may change.'}
