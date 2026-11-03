"""IMF official SDMX 3.0 dataflow discovery, structures and series.

IMF data API: https://data.imf.org/en/Resource-Pages/IMF-API . Data queries
return original SDMX JSON with dimensions and attributes; WEO includes forecasts.
"""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://api.imf.org/external/sdmx/3.0'
MAX_BYTES = 12000000

def _get(path):
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '35', '--max-filesize', str(MAX_BYTES), BASE + path], capture_output=True, timeout=40)
    if r.returncode:
        raise RuntimeError('IMF request failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > MAX_BYTES:
        raise ValueError('IMF response exceeds 12 MB')
    return json.loads(r.stdout)

def _token(x, name, pattern='[A-Za-z0-9_.-]{1,100}'):
    if not isinstance(x, str) or not re.fullmatch(pattern, x):
        raise ValueError('invalid ' + name)
    return x

def dataflows(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('invalid keyword')
    obj = _get('/structure/dataflow/all/all/+')
    flows = obj['data']['dataflows']
    found = [x for x in flows if keyword.casefold() in (x.get('id', '') + ' ' + x.get('name', '')).casefold()]
    return {'source': BASE + '/structure/dataflow/all/all/+', 'total': len(flows), 'matched': len(found), 'dataflows': found}

def structure(agency, flow):
    agency = _token(agency, 'agency')
    flow = _token(flow, 'flow')
    path = '/structure/dataflow/' + agency + '/' + flow + '/+?' + urlencode({'references': 'descendants'})
    return {'source': BASE + path, 'sdmx': _get(path), 'note': 'Full referenced structures and code lists for the current dataflow.'}

def series(agency, flow, key):
    agency = _token(agency, 'agency')
    flow = _token(flow, 'flow')
    key = _token(key, 'series key', '[A-Za-z0-9_+.-]{1,200}')
    if sum((bool(x) for x in key.split('.'))) < 2:
        raise ValueError('key must specify at least two dimensions')
    path = '/data/dataflow/' + agency + '/' + flow + '/+/' + key
    obj = _get(path)
    if not isinstance(obj, dict) or 'data' not in obj:
        raise ValueError('unexpected IMF data response')
    return {'source': BASE + path, 'sdmx': obj, 'note': 'Observation indexes map to TIME_PERIOD in data.structures; series attributes and values retain their SDMX coding. WEO mixes historical estimates and projections.'}
