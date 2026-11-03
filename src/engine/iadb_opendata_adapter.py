"""Inter-American Development Bank Open Data CKAN catalog and datastore API.

Official site https://data.iadb.org/ . Dataset-specific source, methodology,
units and license are in package/resource metadata; consult them for each series.
"""
import release_runtime
import json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://data.iadb.org/api/3/action'
MAX_BYTES = 10000000

def _get(action, params):
    path = '/' + action + '?' + urlencode(params)
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', str(MAX_BYTES), BASE + path], capture_output=True, timeout=35)
    if r.returncode:
        raise RuntimeError('IDB request failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > MAX_BYTES:
        raise ValueError('IDB response exceeds 10 MB')
    obj = json.loads(r.stdout)
    if not isinstance(obj, dict) or obj.get('success') is not True:
        raise RuntimeError('IDB API error: ' + str(obj.get('error', 'unknown'))[:500])
    return {'source': BASE + path, 'result': obj['result']}

def _page(offset, limit):
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (offset, limit))) or offset < 0 or (not 1 <= limit <= 100):
        raise ValueError('offset must be nonnegative and limit 1 to 100')

def search(keyword='', offset=0, limit=20):
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('invalid keyword')
    _page(offset, limit)
    return _get('package_search', {'q': keyword or '*:*', 'start': offset, 'rows': limit})

def dataset(identifier):
    if not isinstance(identifier, str) or not re.fullmatch('[a-zA-Z0-9_-]{1,160}', identifier):
        raise ValueError('invalid dataset identifier')
    return _get('package_show', {'id': identifier})

def records(resource, filters=None, offset=0, limit=20):
    if not isinstance(resource, str) or not re.fullmatch('[0-9a-fA-F-]{36}', resource):
        raise ValueError('resource must be a UUID')
    _page(offset, limit)
    params = {'resource_id': resource, 'offset': offset, 'limit': limit, 'include_total': 'true'}
    if filters is not None:
        if not isinstance(filters, dict) or len(filters) > 10 or any((not isinstance(k, str) or not isinstance(v, (str, int, float)) or isinstance(v, bool) for k, v in filters.items())):
            raise ValueError('invalid filters')
        params['filters'] = json.dumps(filters, ensure_ascii=False, separators=(',', ':'))
    return _get('datastore_search', params)
