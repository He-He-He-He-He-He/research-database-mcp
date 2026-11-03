"""IEA Energy Investment Explorer public webpage API; units from explorer charts."""
import release_runtime
import json
import subprocess
from urllib.parse import urlencode
BASE = 'https://api.iea.org/eiu-finance'
PAGE = 'https://www.iea.org/data-and-statistics/data-tools/investment-data-explorer'
MAX_BYTES = 12000000

def _get(path='', params=None):
    url = BASE + path + ('?' + urlencode(params) if params else '')
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '40', '--max-filesize', str(MAX_BYTES), url], capture_output=True, timeout=45)
    if r.returncode:
        raise RuntimeError('IEA request failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > MAX_BYTES:
        raise ValueError('response too large')
    data = json.loads(r.stdout)
    if not isinstance(data, list):
        raise ValueError('unexpected response')
    return (url, data)

def regions():
    url, rows = _get('/list/region')
    if not all((isinstance(x, str) for x in rows)):
        raise ValueError('unexpected regions')
    return {'source': url, 'explorer': PAGE, 'regions': rows}

def data(region='World', category='Investment spending', start=2015, end=2025):
    if category not in ('Investment spending', 'Instrument', 'Financier', 'Investor'):
        raise ValueError('invalid category')
    if not isinstance(region, str) or not region.strip() or len(region) > 120:
        raise ValueError('invalid region')
    if any((isinstance(x, bool) or not isinstance(x, int) or (not 1900 <= x <= 2100) for x in (start, end))) or start > end:
        raise ValueError('invalid year range')
    filters = {'region': region, 'category': category, 'scenario': 'STEPS'}
    url, rows = _get('', filters)
    if any((not isinstance(row, dict) or any((row.get(k) != v for k, v in filters.items())) or (not isinstance(row.get('year'), int)) for row in rows)):
        raise ValueError('unexpected or out-of-filter result')
    subset = [row for row in rows if start <= row['year'] <= end]
    return {'source': url, 'explorer': PAGE, 'explorer_updated': '2026-05-28', 'unit': 'billion USD (2025, MER)', 'year_filter': 'local', 'rows': subset, 'note': 'Explorer chart labels use 2025 US dollars at market exchange rates; investment estimates and scenario are not actual disbursements. Regions, sectors and financing breakdowns can overlap. API provides no per-row unit or observation status; use official methodology. Website endpoint may change.'}
