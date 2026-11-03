"""IEA public Critical Minerals Explorer material-demand scenario data."""
import release_runtime
import json
import subprocess
from urllib.parse import urlencode
BASE = 'https://api.iea.org/minerals'
PAGE = 'https://www.iea.org/data-and-statistics/data-tools/critical-minerals-data-explorer'
MAX_BYTES = 8000000

def _get(path='', params=None):
    url = BASE + path + ('?' + urlencode(params) if params else '')
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '35', '--max-filesize', str(MAX_BYTES), url], capture_output=True, timeout=40)
    if r.returncode:
        raise RuntimeError('IEA request failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > MAX_BYTES:
        raise ValueError('response too large')
    rows = json.loads(r.stdout)
    if not isinstance(rows, list):
        raise ValueError('unexpected response')
    return (url, rows)

def materials():
    url, rows = _get('/list/material')
    if any((not isinstance(x, str) for x in rows)):
        raise ValueError('unexpected materials')
    return {'source': url, 'page': PAGE, 'materials': rows}

def demand(material, start, end, scenario='Stated Policies Scenario'):
    if not isinstance(material, str) or not material.strip() or len(material) > 120:
        raise ValueError('invalid material')
    if scenario not in ('Stated Policies Scenario', 'Current Policies Scenario', 'High Demand Scenario'):
        raise ValueError('invalid scenario')
    if any((isinstance(x, bool) or not isinstance(x, int) or (not 1900 <= x <= 2100) for x in (start, end))) or start > end:
        raise ValueError('invalid years')
    params = {'material': material, 'flow': 'IDLE', 'case': 'Base Case', 'category': 'Material demand'}
    url, rows = _get('', params)
    if any((not isinstance(r, dict) or any((r.get(k) != v for k, v in params.items())) or (not isinstance(r.get('year'), int)) for r in rows)):
        raise ValueError('unexpected/out-of-filter response')
    chosen = [r for r in rows if r.get('scenario') == scenario and start <= r['year'] <= end]
    return {'source': url, 'page': PAGE, 'page_updated': '2026-07-27', 'local_filters': {'scenario': scenario, 'start': start, 'end': end}, 'rows': chosen, 'note': 'World material-demand model data by product and scenario; future values are projections, not observations. Categories and cases may overlap; retain raw units and do not sum totals and subcategories. Explorer frontend endpoint may change; consult model methodology.'}
