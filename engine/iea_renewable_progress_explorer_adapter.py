"""IEA Renewables 2025 public progress explorer, electricity market data."""
import release_runtime
import json
import subprocess
from urllib.parse import urlencode
BASE = 'https://api.iea.org/renewables/market'
PAGE = 'https://www.iea.org/data-and-statistics/data-tools/renewable-energy-progress-tracker'
MAX_BYTES = 10000000

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

def regions():
    url, rows = _get('/list/region')
    if any((not isinstance(x, str) for x in rows)):
        raise ValueError('unexpected region list')
    return {'source': url, 'page': PAGE, 'regions': rows}

def data(region, flow, start, end, case='MAIN'):
    if any((not isinstance(x, str) or not x.strip() or len(x) > 120 for x in (region, flow, case))):
        raise ValueError('invalid filter')
    if any((isinstance(x, bool) or not isinstance(x, int) or (not 1900 <= x <= 2100) for x in (start, end))) or start > end:
        raise ValueError('invalid years')
    params = {'region': region, 'flow': flow}
    url, rows = _get('', params)
    if any((not isinstance(r, dict) or any((r.get(k) != v for k, v in params.items())) or (not isinstance(r.get('year'), int)) for r in rows)):
        raise ValueError('unexpected/out-of-filter response')
    chosen = [r for r in rows if r.get('case') == case and start <= r['year'] <= end]
    return {'source': url, 'page': PAGE, 'page_updated': '2025-12-15', 'local_filters': {'start': start, 'end': end, 'case': case}, 'rows': chosen, 'note': 'Renewables 2025 webpage labels 2024 last historical year and 2025–2030 forecast. MAIN and ACC are different cases; do not sum. Capacity in GW, generation in TWh, net additions may be negative. Country and regional aggregates, total and components overlap. Preserve raw values and consult methodology.'}
