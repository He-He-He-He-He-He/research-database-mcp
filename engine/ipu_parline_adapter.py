"""Inter-Parliamentary Union Parline API: national parliamentary data.

Official docs: https://data.ipu.org/data-tools/api/ . API metadata states
CC BY-NC-SA 4.0: attribution, non-commercial use, share alike.
"""
import release_runtime
import json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://api.data.ipu.org/v1'
MAX_BYTES = 12000000

def _get(path, params):
    url = BASE + path + '?' + urlencode(params)
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '35', '--max-filesize', str(MAX_BYTES), url], capture_output=True, timeout=40)
    if r.returncode:
        raise RuntimeError('IPU request failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > MAX_BYTES:
        raise ValueError('IPU response exceeds 12 MB')
    obj = json.loads(r.stdout)
    if not isinstance(obj, dict) or 'data' not in obj:
        raise ValueError('unexpected IPU response')
    return {'source': url, 'response': obj, 'note': 'Official data and metadata retained, including access date and reuse licence. Values may change over time.'}

def _page(page, size):
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (page, size))) or page < 1 or (not 1 <= size <= 50):
        raise ValueError('page must be positive and size 1 to 50')
    return [('page[number]', page), ('page[size]', size)]

def fields(page=1, size=20):
    return _get('/metadata/fields/', _page(page, size))

def entities(kind, country=None, page=1, size=10):
    if kind not in ('countries', 'parliaments', 'chambers', 'elections', 'specialized_bodies'):
        raise ValueError('invalid entity type')
    params = _page(page, size)
    if country is not None:
        if not isinstance(country, str) or not re.fullmatch('[A-Z]{2}', country):
            raise ValueError('country must be two uppercase letters')
        params.append(('filter', 'country_code:eq:' + country))
    return _get('/' + kind, params)
