"""data.gov.scot catalogue and unfiltered datastore pages."""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://api.data.gov.scot/api/3/action/'

def _request(action, params):
    url = BASE + action + '?' + urlencode(params)
    p = release_runtime.run(['/usr/bin/curl', '-q', '--compressed', '-fsSL', '--max-time', '30', '--max-filesize', '8388608', url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('data.gov.scot request failed: ' + p.stderr.decode('utf8', 'replace').strip())
    if len(p.stdout) > 8388608:
        raise RuntimeError('Response exceeds 8 MiB')
    data = json.loads(p.stdout)
    if not data.get('success'):
        raise RuntimeError('data.gov.scot returned error: ' + str(data.get('error')))
    return data['result']

def search(query, start=0, rows=20):
    if not isinstance(query, str) or len(query) > 200 or isinstance(start, bool) or (not isinstance(start, int)) or (start < 0) or isinstance(rows, bool) or (not isinstance(rows, int)) or (not 1 <= rows <= 100):
        raise ValueError('Invalid query or pagination')
    return _request('package_search', {'q': query, 'start': start, 'rows': rows})

def dataset(dataset_id):
    if not isinstance(dataset_id, str) or not re.fullmatch('[A-Za-z0-9_-]+', dataset_id):
        raise ValueError('Invalid dataset identifier')
    return _request('package_show', {'id': dataset_id})

def page(resource_id, offset=0, limit=100):
    if not isinstance(resource_id, str) or not re.fullmatch('[0-9a-fA-F-]{36}', resource_id):
        raise ValueError('Invalid resource UUID')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 1000):
        raise ValueError('Invalid pagination')
    return _request('datastore_search', {'resource_id': resource_id, 'offset': offset, 'limit': limit})
