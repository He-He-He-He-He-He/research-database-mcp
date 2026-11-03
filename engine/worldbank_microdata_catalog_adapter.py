"""World Bank Microdata Library catalog: country search and survey metadata.

Catalog includes studies from other institutions; actual microdata availability
and access conditions vary. This adapter retrieves catalog metadata only.
Official portal: https://microdata.worldbank.org/home
"""
import release_runtime
import json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://microdata.worldbank.org/index.php/api/catalog'
MAX_BYTES = 8000000

def _get(path, params=None):
    url = BASE + path + ('?' + urlencode(params) if params else '')
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', '--max-filesize', str(MAX_BYTES), url], capture_output=True, timeout=30)
    if r.returncode:
        raise RuntimeError('World Bank microdata API failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > MAX_BYTES:
        raise ValueError('microdata metadata exceeds 8 MB')
    obj = json.loads(r.stdout)
    if obj.get('status') != 'success':
        raise ValueError('World Bank API error: ' + str(obj.get('message', 'unknown')))
    return {'source': url, 'response': obj, 'note': 'Catalog metadata only: publication does not imply unrestricted access to the underlying survey files.'}

def search(country, page=1, page_size=15):
    if not isinstance(country, str) or not re.fullmatch('[A-Za-z .,-]{2,100}', country):
        raise ValueError('country must be a country name')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (page, page_size))) or page < 1 or (not 1 <= page_size <= 100):
        raise ValueError('page must be positive and page_size 1 to 100')
    data = _get('/search', {'country': country, 'page': page, 'ps': page_size})
    result = data['response'].get('result', {})
    if not isinstance(result.get('rows'), list) or result.get('page') != page:
        raise ValueError('unexpected catalog pagination')
    return data

def detail(idno):
    if not isinstance(idno, str) or not re.fullmatch('[A-Za-z0-9_.-]{1,150}', idno):
        raise ValueError('invalid survey identifier')
    data = _get('/' + idno)
    if data['response'].get('dataset', {}).get('idno') != idno:
        raise ValueError('unexpected dataset identifier')
    return data
