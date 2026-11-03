"""UNdata SDMX REST catalog, structures and bounded data queries.

Official documentation: https://data.un.org/Host.aspx?Content=API
UN energy data terms: https://unstats.un.org/unsd/energy/edbase.htm
Only dataflows exposed by the UNdata API are available, not every datamart.
"""
import release_runtime
import csv
import io
import re
import subprocess
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
BASE = 'https://data.un.org/ws/rest'
MAX_BYTES = 10000000

def _get(path):
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--location', '--proto-redir', '=https', '--max-time', '30', '--max-filesize', str(MAX_BYTES), BASE + path], capture_output=True, timeout=35)
    if r.returncode:
        raise RuntimeError('UNdata request failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > MAX_BYTES:
        raise ValueError('UNdata response too large')
    return r.stdout.decode('utf-8-sig')

def _token(v, label, pattern='[A-Za-z0-9_-]{1,100}'):
    if not isinstance(v, str) or not re.fullmatch(pattern, v):
        raise ValueError('invalid ' + label)
    return v

def dataflows(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('invalid keyword')
    root = ET.fromstring(_get('/dataflow/'))
    out = []
    for x in root.iter():
        if x.tag.split('}')[-1] != 'Dataflow':
            continue
        item = {'id': x.get('id'), 'agency': x.get('agencyID'), 'version': x.get('version')}
        names = [y.text for y in x if y.tag.split('}')[-1] == 'Name']
        item['name'] = names[0] if names else ''
        refs = [y.attrib for y in x.iter() if y.tag.split('}')[-1] == 'Ref']
        item['structure'] = refs[0] if refs else None
        if keyword.casefold() in (item['id'] + ' ' + item['name']).casefold():
            out.append(item)
    return {'source': BASE + '/dataflow/', 'dataflows': out, 'matched': len(out)}

def structure(agency, structure_id, version='latest'):
    agency = _token(agency, 'agency')
    structure_id = _token(structure_id, 'structure')
    version = _token(version, 'version', '(?:latest|[0-9]+(?:\\.[0-9]+)*)')
    path = '/datastructure/' + agency + '/' + structure_id + '/' + version + '?references=children'
    xml = _get(path)
    ET.fromstring(xml)
    return {'source': BASE + path, 'sdmx_xml': xml, 'note': 'Original SDMX structure and referenced codelists; dimension order and code meanings depend on the dataflow.'}

def data(agency, flow, version, key, start, end):
    agency = _token(agency, 'agency')
    flow = _token(flow, 'flow')
    version = _token(version, 'version', '[0-9]+(?:\\.[0-9]+)*')
    key = _token(key, 'series key', '[A-Za-z0-9_+.-]{1,200}')
    if any((isinstance(x, bool) or not isinstance(x, int) or (not 1800 <= x <= 2100) for x in (start, end))) or start > end:
        raise ValueError('invalid years')
    path = '/data/' + agency + ',' + flow + ',' + version + '/' + key + '/ALL/?' + urlencode({'startPeriod': start, 'endPeriod': end, 'format': 'csv'})
    raw = _get(path)
    if raw.lstrip().startswith('<'):
        raise RuntimeError('UNdata returned XML rather than CSV: ' + raw[:400])
    reader = csv.DictReader(io.StringIO(raw))
    if not reader.fieldnames or not {'DATAFLOW', 'TIME_PERIOD', 'OBS_VALUE'}.issubset(reader.fieldnames):
        raise ValueError('unexpected UNdata CSV response')
    return {'source': BASE + path, 'observations': list(reader), 'note': 'Original columns and attributes retained. Consult structure for codes and units.'}
