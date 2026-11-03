"""ECB public SDMX catalog, structure and time-bounded data queries.

Official docs: https://data.ecb.europa.eu/help/api/overview . Preserve ECB's
units, observation status, source descriptions and other CSV attributes.
"""
import release_runtime
import csv
import io
import re
import subprocess
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
BASE = 'https://data-api.ecb.europa.eu/service'
MAX_BYTES = 12000000

def _get(path):
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '35', '--max-filesize', str(MAX_BYTES), '--write-out', '\n%{http_code}', BASE + path], capture_output=True, timeout=40)
    if r.returncode:
        raise RuntimeError('ECB request failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    body, status = r.stdout.rsplit(b'\n', 1)
    if len(body) > MAX_BYTES:
        raise ValueError('ECB response too large')
    return None if status == b'204' else body.decode('utf-8-sig')

def _token(v, name, pattern='[A-Za-z0-9_]{1,100}'):
    if not isinstance(v, str) or not re.fullmatch(pattern, v):
        raise ValueError('invalid ' + name)
    return v

def dataflows(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('invalid keyword')
    root = ET.fromstring(_get('/dataflow'))
    out = []
    total = 0
    for x in root.iter():
        if x.tag.split('}')[-1] != 'Dataflow':
            continue
        total += 1
        names = [y.text or '' for y in x if y.tag.split('}')[-1] == 'Name' and y.get('{http://www.w3.org/XML/1998/namespace}lang') == 'en']
        name = names[0] if names else ''
        code = x.get('id', '')
        if keyword.casefold() in (code + ' ' + name).casefold():
            out.append({'id': code, 'agency': x.get('agencyID'), 'version': x.get('version'), 'name': name, 'structure': next((y.attrib for y in x.iter() if y.tag.split('}')[-1] == 'Ref'), None)})
    return {'source': BASE + '/dataflow', 'total': total, 'matched': len(out), 'dataflows': out}

def structure(agency, identifier, version='latest'):
    agency = _token(agency, 'agency')
    identifier = _token(identifier, 'structure')
    version = _token(version, 'version', '(?:latest|[0-9]+(?:\\.[0-9]+)*)')
    path = '/datastructure/' + agency + '/' + identifier + '/' + version + '?references=children'
    xml = _get(path)
    if xml is None:
        raise ValueError('structure not found')
    ET.fromstring(xml)
    return {'source': BASE + path, 'sdmx_xml': xml}

def series(flow, key, start, end):
    flow = _token(flow, 'flow')
    key = _token(key, 'series key', '[A-Za-z0-9_+.-]{1,200}')
    for x in (start, end):
        _token(x, 'period', '[0-9]{4}(?:-(?:[0-9]{2}|Q[1-4]|S[1-2])(?:-[0-9]{2})?)?')
    if start > end:
        raise ValueError('invalid period range')
    if sum((bool(x) for x in key.split('.'))) < 2:
        raise ValueError('key must specify at least two dimensions')
    path = '/data/' + flow + '/' + key + '?' + urlencode({'startPeriod': start, 'endPeriod': end, 'format': 'csvdata'})
    raw = _get(path)
    if raw is None:
        return {'source': BASE + path, 'observations': []}
    if raw.lstrip().startswith('<'):
        raise RuntimeError('ECB returned XML instead of CSV: ' + raw[:300])
    reader = csv.DictReader(io.StringIO(raw))
    if not reader.fieldnames or not {'KEY', 'TIME_PERIOD', 'OBS_VALUE', 'UNIT', 'UNIT_MULT'}.issubset(reader.fieldnames):
        raise ValueError('unexpected ECB CSV response')
    return {'source': BASE + path, 'observations': list(reader), 'note': 'Retains ECB unit, unit multiplier, observation status, title and all supplied qualifiers.'}
