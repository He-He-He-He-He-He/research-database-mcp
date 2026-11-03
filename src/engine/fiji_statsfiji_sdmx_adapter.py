"""Fiji Bureau of Statistics official Data Hub public SDMX.

Docs: https://sis-cc.gitlab.io/dotstatsuite-documentation/using-api/restful/
Source and reuse rights vary by dataflow.
"""
import release_runtime
import csv, io, re, subprocess, xml.etree.ElementTree as ET
from urllib.parse import urlencode
BASE = 'https://data-sdmx-disseminate.statsfiji.gov.fj/rest'
MAX_BYTES = 12000000

def _get(path):
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '35', '--max-filesize', str(MAX_BYTES), '--write-out', '\n%{http_code}', BASE + path], capture_output=True, timeout=40)
    if r.returncode:
        raise RuntimeError('Fiji Data Hub request failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
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
            out.append({'id': code, 'name': name, 'agency': x.get('agencyID'), 'version': x.get('version'), 'structure': next((y.attrib for y in x.iter() if y.tag.split('}')[-1] == 'Ref'), None)})
    return {'source': BASE + '/dataflow', 'total': total, 'matched': len(out), 'dataflows': out}

def structure(agency, identifier, version):
    agency = _token(agency, 'agency')
    identifier = _token(identifier, 'structure')
    version = _token(version, 'version', '[0-9]+(?:\\.[0-9]+)*')
    path = '/datastructure/' + agency + '/' + identifier + '/' + version + '?references=children'
    xml = _get(path)
    if xml is None:
        raise ValueError('structure not found')
    ET.fromstring(xml)
    return {'source': BASE + path, 'sdmx_xml': xml}

def data(agency, flow, version, key, start, end):
    agency = _token(agency, 'agency')
    flow = _token(flow, 'flow')
    version = _token(version, 'version', '[0-9]+(?:\\.[0-9]+)*')
    key = _token(key, 'key', '[A-Za-z0-9_+.-]{1,200}')
    if sum((bool(x) for x in key.split('.'))) < 2:
        raise ValueError('specify at least two dimensions')
    if any((isinstance(x, bool) or not isinstance(x, int) or (not 1800 <= x <= 2100) for x in (start, end))) or start > end:
        raise ValueError('invalid year range')
    path = '/data/' + agency + ',' + flow + ',' + version + '/' + key + '?' + urlencode({'startPeriod': start, 'endPeriod': end, 'format': 'csv'})
    raw = _get(path)
    if raw is None:
        return {'source': BASE + path, 'observations': []}
    if raw.lstrip().startswith('<'):
        raise RuntimeError('upstream returned XML rather than CSV: ' + raw[:300])
    reader = csv.DictReader(io.StringIO(raw))
    if not reader.fieldnames or not {'DATAFLOW', 'TIME_PERIOD', 'OBS_VALUE'}.issubset(reader.fieldnames):
        raise ValueError('unexpected Fiji Data Hub CSV')
    return {'source': BASE + path, 'observations': list(reader), 'note': 'Dataflow structure defines dimension order and codes; units, base periods, notes and source fields remain unchanged.'}
