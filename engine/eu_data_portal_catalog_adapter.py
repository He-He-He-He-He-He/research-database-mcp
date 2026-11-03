"""European Commission data.europa.eu read-only metadata search API."""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://data.europa.eu/api/hub/search/'

def _get(path, params=None):
    u = BASE + path + ('?' + urlencode(params) if params else '')
    p = release_runtime.run(['curl', '--compressed', '-fsSL', '--max-time', '30', '--max-filesize', '8388608', u], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('EU portal request failed: ' + p.stderr.decode('utf8', 'replace').strip())
    if len(p.stdout) > 8388608:
        raise RuntimeError('Response exceeds 8 MiB')
    return json.loads(p.stdout)

def search(query, page=0, limit=10, kind='dataset'):
    if not isinstance(page, int) or page < 0 or (not isinstance(limit, int)) or (not 1 <= limit <= 100):
        raise ValueError('Invalid page or limit')
    if kind not in ('dataset', 'dataservice', 'catalogue', 'organization'):
        raise ValueError('Invalid kind')
    return _get('search', {'q': query, 'page': page, 'limit': limit, 'filters': kind})

def dataset(identifier):
    if not isinstance(identifier, str) or not re.fullmatch('[A-Za-z0-9_-]+', identifier):
        raise ValueError('Invalid identifier')
    return _get('datasets/' + identifier)
