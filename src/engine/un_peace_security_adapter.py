"""UN Peace and Security Data Hub: public dataset metadata and records.

Official API: https://psdata.un.org/howto/api_structure . Data represent distinct
UN operations and indicators with individual collection scopes, dates and licences.
"""
import release_runtime
import json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://api.psdata.un.org/public'
MAX_BYTES = 10000000

def _get(path, params=None):
    url = BASE + path + ('?' + urlencode(params) if params else '')
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', str(MAX_BYTES), url], capture_output=True, timeout=35)
    if r.returncode:
        raise RuntimeError('UN peace data API failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > MAX_BYTES:
        raise ValueError('response exceeds 10 MB')
    obj = json.loads(r.stdout)
    if not isinstance(obj, (dict, list)):
        raise ValueError('unexpected UN peace data response')
    return {'source': url, 'response': obj, 'note': 'Consult dataset metadata for definitions, coverage, collection date and terms.'}

def _id(v):
    if not isinstance(v, str) or not re.fullmatch('[A-Za-z0-9_-]{1,100}', v):
        raise ValueError('invalid dataset ID')
    return v

def metadata(dataset='all'):
    return _get('/metadata/' + _id(dataset))

def data(dataset, page=1, per_page=20, field=None, value=None):
    _id(dataset)
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (page, per_page))) or page < 1 or (not 1 <= per_page <= 100):
        raise ValueError('page must be positive and per_page 1 to 100')
    params = {'page_num': page, 'per_page': per_page}
    if (field is None) != (value is None):
        raise ValueError('field and value must be supplied together')
    if field is not None:
        if not isinstance(field, str) or not re.fullmatch('[A-Za-z0-9_]{1,80}', field):
            raise ValueError('invalid filter field')
        if not isinstance(value, str) or not re.fullmatch('[A-Za-z0-9_ -]{1,100}', value):
            raise ValueError('invalid filter value')
        params['filter'] = field + ':' + value
    return _get('/data/' + dataset + '/json', params)
