"""Read-only dataset catalogue from Serbia's national open data portal."""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://data.gov.rs/api/1/datasets/'
MAX_RESPONSE = 8 * 1024 * 1024

def _get(url):
    proc = release_runtime.run(['curl', '--compressed', '-fsS', '--max-time', '30', '--max-filesize', str(MAX_RESPONSE), url], capture_output=True, timeout=35)
    if proc.returncode:
        raise RuntimeError('Serbia open data portal request failed: ' + proc.stderr.decode('utf-8', 'replace').strip())
    if len(proc.stdout) > MAX_RESPONSE:
        raise RuntimeError('Serbia open data response exceeds 8 MiB')
    data = json.loads(proc.stdout)
    if not isinstance(data, dict):
        raise RuntimeError('Unexpected response format')
    return data

def search(query, page=1, page_size=10):
    if not isinstance(query, str) or len(query) > 200:
        raise ValueError('query must be a string at most 200 characters')
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise ValueError('page must be a positive integer')
    if isinstance(page_size, bool) or not isinstance(page_size, int) or (not 1 <= page_size <= 100):
        raise ValueError('page_size must be between 1 and 100')
    data = _get(BASE + '?' + urlencode({'q': query, 'page': page, 'page_size': page_size}))
    if not isinstance(data.get('data'), list) or 'total' not in data:
        raise RuntimeError('Unexpected catalogue result')
    return {'source': 'Serbia national open data portal', 'source_info': 'https://data.gov.rs/sr/apidoc/', 'query': query, 'result': data, 'note': 'Dataset metadata only; verify organization, original resources and license. Results may contain non-statistical datasets; source files are not fetched.'}

def dataset(identifier):
    if not isinstance(identifier, str) or not re.fullmatch('[A-Za-z0-9_-]{1,150}', identifier):
        raise ValueError('Invalid dataset identifier')
    data = _get(BASE + identifier + '/')
    if not data.get('id') or not isinstance(data.get('resources'), list):
        raise RuntimeError('Unexpected dataset result')
    return {'source': 'Serbia national open data portal', 'source_info': 'https://data.gov.rs/sr/apidoc/', 'dataset': data, 'note': 'Dataset metadata only; resource URLs and rights must be verified individually; no source data are retrieved.'}
