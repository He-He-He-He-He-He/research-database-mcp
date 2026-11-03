"""India Census digital library aggregated tables API (experimental upstream)."""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://censusindia.gov.in/nada/index.php/api/tables/'

def _year(year):
    if str(year) not in ('2001', '2011'):
        raise ValueError('Only census years 2001 and 2011 are documented')
    return str(year)

def _table(table):
    if not isinstance(table, str) or not re.fullmatch('[A-Za-z0-9_-]+', table):
        raise ValueError('Invalid table ID')
    return table

def _fetch(path, params=None):
    url = BASE + path + ('?' + urlencode(params) if params else '')
    proc = release_runtime.run(['/usr/bin/curl', '-q', '--compressed', '-fsSL', '--max-time', '35', '--max-filesize', '8388608', url], capture_output=True, timeout=40)
    if proc.returncode:
        raise RuntimeError('India Census request failed: ' + proc.stderr.decode('utf8', 'replace').strip())
    if len(proc.stdout) > 8388608:
        raise RuntimeError('Response exceeds 8 MiB')
    payload = json.loads(proc.stdout)
    if payload.get('status') not in (None, 'success'):
        raise RuntimeError('India Census returned an error: ' + str(payload.get('status')))
    return payload

def catalog(year=2011):
    return _fetch('list/' + _year(year) + '/')

def metadata(table, year=2011):
    return _fetch('info/' + _year(year) + '/' + _table(table))

def observations(table, filters, year=2011, limit=100):
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 1000):
        raise ValueError('limit must be 1–1000')
    if not isinstance(filters, dict) or not filters:
        raise ValueError('At least one selective filter is required')
    if any((not re.fullmatch('[A-Za-z][A-Za-z0-9_]*', str(k)) or not re.fullmatch('[A-Za-z0-9_,.\\-]+', str(v)) for k, v in filters.items())):
        raise ValueError('Invalid filter name or value')
    return _fetch('data/' + _year(year) + '/' + _table(table) + '/' + str(limit), filters)
