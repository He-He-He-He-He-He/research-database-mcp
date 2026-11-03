"""UNICEF SDMX registry: discover all public dataflows and query bounded data.

Official docs: https://data.unicef.org/sdmx-api-documentation/ . The registry
includes some UN population division and regional flows; sources vary by row.
"""
import release_runtime
import csv, io, json, re, subprocess, xml.etree.ElementTree as ET
from urllib.parse import urlencode
BASE = 'https://sdmx.data.unicef.org/ws/public/sdmxapi/rest'
MAX_BYTES = 12000000

def _get(path):
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '35', '--max-filesize', str(MAX_BYTES), '--write-out', '\n%{http_code}', BASE + path], capture_output=True, timeout=40)
    if r.returncode:
        raise RuntimeError('UNICEF SDMX request failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    raw, status = r.stdout.rsplit(b'\n', 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('response exceeds 12 MB')
    return None if status == b'204' else raw.decode('utf-8-sig')

def _token(v, name, pattern='[A-Za-z0-9_]{1,100}'):
    if not isinstance(v, str) or not re.fullmatch(pattern, v):
        raise ValueError('invalid ' + name)
    return v

def dataflows(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('invalid keyword')
    path = '/dataflow/all/all/latest/?format=sdmx-json'
    obj = json.loads(_get(path))
    flows = obj['data']['dataflows']
    result = [x for x in flows if keyword.casefold() in (str(x.get('id', '')) + ' ' + str(x.get('name', ''))).casefold()]
    return {'source': BASE + path, 'total': len(flows), 'matched': len(result), 'dataflows': result}

def structure(agency, flow):
    agency = _token(agency, 'agency')
    flow = _token(flow, 'flow')
    path = '/dataflow/' + agency + '/' + flow + '/latest/?references=all&format=sdmx-json'
    raw = _get(path)
    if raw is None:
        raise ValueError('dataflow structure not found')
    return {'source': BASE + path, 'sdmx': json.loads(raw)}

def data(agency, flow, version, key, start, end):
    agency = _token(agency, 'agency')
    flow = _token(flow, 'flow')
    version = _token(version, 'version', '[0-9]+(?:\\.[0-9]+)*')
    key = _token(key, 'key', '[A-Za-z0-9_+.-]{1,200}')
    if sum((bool(x) for x in key.split('.'))) < 2:
        raise ValueError('at least two dimensions must be specified')
    if any((isinstance(x, bool) or not isinstance(x, int) or (not 1800 <= x <= 2100) for x in (start, end))) or start > end:
        raise ValueError('invalid year range')
    path = '/data/' + agency + ',' + flow + ',' + version + '/' + key + '?' + urlencode({'startPeriod': start, 'endPeriod': end, 'format': 'csv'})
    raw = _get(path)
    if raw is None:
        return {'source': BASE + path, 'observations': []}
    if raw.lstrip().startswith('<'):
        raise RuntimeError('UNICEF returned XML instead of CSV: ' + raw[:300])
    reader = csv.DictReader(io.StringIO(raw))
    if not reader.fieldnames or not {'TIME_PERIOD', 'OBS_VALUE'}.issubset(reader.fieldnames):
        raise ValueError('unexpected UNICEF CSV')
    return {'source': BASE + path, 'observations': list(reader), 'note': 'Read flow structure for dimension codes and units. Values may be estimates or projections; retain source and status.'}
