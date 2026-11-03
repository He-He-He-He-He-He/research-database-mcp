"""ILO public SDMX generic flow discovery, metadata and data queries.

Official API: https://sdmx.ilo.org/index.html ; returned attributes retain units,
source and methodological qualifiers. Dataflows vary by dimensions and coverage.
"""
import release_runtime
import csv
import io
import re
import subprocess
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
BASE = 'https://sdmx.ilo.org/rest'
MAX_BYTES = 15000000

def _get(path):
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '40', '--max-filesize', str(MAX_BYTES), '--write-out', '\n%{http_code}', BASE + path], capture_output=True, timeout=45)
    if r.returncode:
        raise RuntimeError('ILO request failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    raw, status = r.stdout.rsplit(b'\n', 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('ILO response too large')
    return None if status == b'204' else raw.decode('utf-8-sig')

def _token(x, name, pattern='[A-Za-z0-9_]{1,100}'):
    if not isinstance(x, str) or not re.fullmatch(pattern, x):
        raise ValueError('invalid ' + name)
    return x

def dataflows(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('invalid keyword')
    root = ET.fromstring(_get('/dataflow/ILO/all/latest'))
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
            out.append({'id': code, 'name': name, 'version': x.get('version'), 'agency': x.get('agencyID'), 'structure': next((y.attrib for y in x.iter() if y.tag.split('}')[-1] == 'Ref'), None)})
    return {'source': BASE + '/dataflow/ILO/all/latest', 'total': total, 'matched': len(out), 'dataflows': out}

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

def data(flow, key, start, end):
    flow = _token(flow, 'flow')
    key = _token(key, 'key', '[A-Za-z0-9_+.-]{1,200}')
    if len([x for x in key.split('.') if x]) < 2:
        raise ValueError('select at least two dimensions')
    if any((isinstance(x, bool) or not isinstance(x, int) or (not 1800 <= x <= 2100) for x in (start, end))) or start > end or end - start > 20:
        raise ValueError('invalid year range (maximum 21 years)')
    path = '/data/ILO,' + flow + '/' + key + '?' + urlencode({'startPeriod': start, 'endPeriod': end, 'format': 'csv'})
    raw = _get(path)
    if raw is None:
        return {'source': BASE + path, 'observations': []}
    if raw.lstrip().startswith('<'):
        raise RuntimeError('ILO returned XML instead of CSV: ' + raw[:300])
    reader = csv.DictReader(io.StringIO(raw))
    if not reader.fieldnames or not {'DATAFLOW', 'TIME_PERIOD', 'OBS_VALUE'}.issubset(reader.fieldnames):
        raise ValueError('unexpected ILO CSV response')
    return {'source': BASE + path, 'observations': list(reader), 'note': 'Use the flow structure to resolve dimensions and codes; retain units, source and notes.'}
