"""IEA Methane Tracker public explorer time-series estimates."""
import release_runtime
import json
import subprocess
from urllib.parse import urlencode
BASE = 'https://api.iea.org/methane'
PAGE = 'https://www.iea.org/data-and-statistics/data-tools/methane-tracker'
MAX_BYTES = 8000000

def _get(path, params=None):
    url = BASE + path + ('?' + urlencode(params) if params else '')
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '35', '--max-filesize', str(MAX_BYTES), url], capture_output=True, timeout=40)
    if r.returncode:
        raise RuntimeError('IEA request failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > MAX_BYTES:
        raise ValueError('response too large')
    rows = json.loads(r.stdout)
    if not isinstance(rows, list) or any((not isinstance(x, dict) for x in rows)):
        raise ValueError('unexpected response')
    return (url, rows)

def countries():
    url, rows = _get('/countries')
    return {'source': url, 'explorer': PAGE, 'rows': rows}

def timeseries(country, start, end, scenario='Stated Policies Scenario'):
    if not isinstance(country, str) or not country.strip() or len(country) > 120:
        raise ValueError('invalid country')
    if not isinstance(scenario, str) or not scenario.strip() or len(scenario) > 120:
        raise ValueError('invalid scenario')
    if any((isinstance(x, bool) or not isinstance(x, int) or (not 1900 <= x <= 2100) for x in (start, end))) or start > end:
        raise ValueError('invalid years')
    params = {'country': country, 'scenario': scenario}
    url, rows = _get('/timeseries', params)
    if any((r.get('country') != country or r.get('scenario') != scenario or (not str(r.get('year', '')).isdigit()) for r in rows)):
        raise ValueError('unexpected/out-of-filter response')
    selected = [r for r in rows if start <= int(r['year']) <= end]
    return {'source': url, 'explorer': PAGE, 'page_updated': '2026-05-04', 'year_filter': 'local', 'rows': selected, 'note': 'IEA estimates and scenario trajectories, not direct observations. Historical years and future projections must be distinguished; preserve source units, products, update dates and source methodology. Time-series endpoint used by webpage may change; third-party content may carry separate rights.'}
