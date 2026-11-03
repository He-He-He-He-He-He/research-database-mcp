"""KAPSARC Energy Data Portal public catalog, metadata and records.

Official API: https://datasource.kapsarc.org/api-console/explore/v2.1/ .
Each dataset has its own publisher, coverage, licence, units and methodology.
"""
import release_runtime
import json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://datasource.kapsarc.org/api/explore/v2.1/catalog/datasets'
MAX_BYTES = 10000000

def _get(path, params):
    url = BASE + path + '?' + urlencode(params)
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', str(MAX_BYTES), url], capture_output=True, timeout=35)
    if r.returncode:
        raise RuntimeError('KAPSARC API failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > MAX_BYTES:
        raise ValueError('response exceeds 10 MB')
    obj = json.loads(r.stdout)
    if not isinstance(obj, dict) or obj.get('error_code'):
        raise ValueError('KAPSARC API error: ' + str(obj)[:300])
    return {'source': url, 'response': obj}

def _id(s):
    if not isinstance(s, str) or not re.fullmatch('[A-Za-z0-9_-]{1,120}', s):
        raise ValueError('invalid dataset ID')
    return s

def _page(offset, limit):
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (offset, limit))) or offset < 0 or (not 1 <= limit <= 100):
        raise ValueError('offset must be nonnegative; limit 1 to 100')
    return {'offset': offset, 'limit': limit}

def search(keyword, offset=0, limit=20):
    if not isinstance(keyword, str) or not re.fullmatch('[A-Za-z0-9 -]{1,100}', keyword):
        raise ValueError('invalid keyword')
    p = _page(offset, limit)
    p['where'] = 'search("' + keyword + '")'
    return _get('', p)

def metadata(dataset):
    return _get('/' + _id(dataset), {})

def records(dataset, offset=0, limit=20, field=None, value=None):
    p = _page(offset, limit)
    if (field is None) != (value is None):
        raise ValueError('field and value must be provided together')
    if field is not None:
        if not isinstance(field, str) or not re.fullmatch('[A-Za-z][A-Za-z0-9_]{0,79}', field):
            raise ValueError('invalid field')
        if not isinstance(value, str) or not re.fullmatch('[A-Za-z0-9_. -]{1,100}', value):
            raise ValueError('invalid value')
        p['where'] = field + "='" + value + "'"
    r = _get('/' + _id(dataset) + '/records', p)
    if not isinstance(r['response'].get('results'), list):
        raise ValueError('unexpected KAPSARC records response')
    r['note'] = 'Publisher, units, licence, update time and methodology are dataset-specific; consult metadata. Records retain all fields.'
    return r
