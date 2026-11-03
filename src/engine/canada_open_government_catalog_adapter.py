"""Government of Canada Open Government read-only catalogue API."""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://open.canada.ca/data/en/api/3/action/'

def _get(action, params):
    url = BASE + action + '?' + urlencode(params)
    p = release_runtime.run(['curl', '--compressed', '-fsSL', '--max-time', '30', '--max-filesize', '8388608', url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('Canada open government request failed: ' + p.stderr.decode('utf8', 'replace').strip())
    if len(p.stdout) > 8388608:
        raise RuntimeError('Response exceeds 8 MiB')
    result = json.loads(p.stdout)
    if not result.get('success'):
        raise RuntimeError('Canada open government error: ' + str(result.get('error')))
    return result['result']

def search(query, start=0, rows=20):
    if not isinstance(start, int) or start < 0 or (not isinstance(rows, int)) or (not 1 <= rows <= 100):
        raise ValueError('Invalid pagination')
    return _get('package_search', {'q': query, 'start': start, 'rows': rows})

def dataset(identifier):
    if not isinstance(identifier, str) or not re.fullmatch('[A-Za-z0-9_-]+', identifier):
        raise ValueError('Invalid dataset ID')
    return _get('package_show', {'id': identifier})
