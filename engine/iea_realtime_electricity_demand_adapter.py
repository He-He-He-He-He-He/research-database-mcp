"""IEA real-time electricity tracker: demand time series, public explorer endpoint."""
import release_runtime
from datetime import date
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://api.iea.org/rte'
PAGE = 'https://www.iea.org/data-and-statistics/data-tools/real-time-electricity-tracker'
LIMIT = 5000000

def _get(path, params=None):
    url = BASE + path + ('?' + urlencode(params) if params else '')
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '35', '--max-filesize', str(LIMIT), url], capture_output=True, timeout=40)
    if r.returncode:
        raise RuntimeError('IEA request failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > LIMIT:
        raise ValueError('response too large')
    value = json.loads(r.stdout)
    return (url, value)

def countries():
    url, rows = _get('/list/countries')
    if not isinstance(rows, list) or any((not isinstance(x, dict) for x in rows)):
        raise ValueError('unexpected countries')
    return {'source': url, 'page': PAGE, 'rows': rows}

def demand(country, start, end, precision='day'):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be ISO3')
    if precision not in ('hour', 'day', 'week'):
        raise ValueError('invalid precision')
    try:
        a = date.fromisoformat(start)
        b = date.fromisoformat(end)
    except (ValueError, TypeError):
        raise ValueError('dates must be YYYY-MM-DD')
    if a > b or (b - a).days > 31:
        raise ValueError('date range must be at most 31 days')
    url, rows = _get('/demand/timeseries', {'ISO3': country, 'from': start, 'to': end, 'precision': precision})
    if not isinstance(rows, list) or any((not isinstance(x, dict) or x.get('ISO3') != country for x in rows)):
        raise ValueError('unexpected/out-of-filter response')
    return {'source': url, 'page': PAGE, 'unit_from_chart': 'GW', 'rows': rows, 'note': 'IEA tracker republishes source grid data; Date and Value are retained unchanged. Chart labels demand in GW, not GWh. Precision is source aggregation; check timezone, source coverage, revisions, and original provider. Empty result is not zero; tracker may lag and webpage endpoint may change.'}
