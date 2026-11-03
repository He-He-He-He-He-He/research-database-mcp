"""UNESCO DataHub public datasets, metadata and records API.

Official API console: https://data.unesco.org/api-console/explore/v2.1/
Datasets and third-party sources have distinct licences and units; inspect metadata.
"""
import release_runtime
import json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://data.unesco.org/api/explore/v2.1/catalog/datasets'
MAX_BYTES = 10000000

def _get(path, params):
    url = BASE + path + '?' + urlencode(params)
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', str(MAX_BYTES), url], capture_output=True, timeout=35)
    if r.returncode:
        raise RuntimeError('UNESCO DataHub request failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > MAX_BYTES:
        raise ValueError('response exceeds 10 MB')
    obj = json.loads(r.stdout)
    if not isinstance(obj, dict) or obj.get('error_code'):
        raise ValueError('UNESCO API error: ' + str(obj)[:500])
    return {'source': url, 'response': obj}

def _id(v):
    if not isinstance(v, str) or not re.fullmatch('[A-Za-z0-9_-]{1,80}', v):
        raise ValueError('invalid dataset ID')
    return v

def _page(offset, limit):
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (offset, limit))) or offset < 0 or (not 1 <= limit <= 100):
        raise ValueError('offset must be nonnegative and limit 1 to 100')
    return {'offset': offset, 'limit': limit}

def datasets(offset=0, limit=20):
    return _get('', _page(offset, limit))

def metadata(dataset):
    return _get('/' + _id(dataset), {})

def records(dataset, offset=0, limit=20, field=None, value=None):
    params = _page(offset, limit)
    if (field is None) != (value is None):
        raise ValueError('field and value must be supplied together')
    if field is not None:
        if not isinstance(field, str) or not re.fullmatch('[A-Za-z][A-Za-z0-9_]{0,79}', field):
            raise ValueError('invalid field')
        if not isinstance(value, str) or not re.fullmatch('[A-Za-z0-9_.-]{1,100}', value):
            raise ValueError('invalid field value')
        params['where'] = field + "='" + value + "'"
    result = _get('/' + _id(dataset) + '/records', params)
    if not isinstance(result['response'].get('results'), list):
        raise ValueError('unexpected UNESCO records response')
    result['note'] = 'Consult dataset metadata for field definitions, source and licence; results preserve all original columns and qualifiers.'
    return result
