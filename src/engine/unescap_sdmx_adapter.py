"""UN ESCAP Data Explorer public SDMX dataflows, definitions and observations.

Official endpoint: https://api-dataexplorer.unescap.org/ . Inspect the returned
structure before querying; several flows are marked NonProductionDataflow.
"""
import release_runtime
import csv
import io
import re
import subprocess
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
BASE = 'https://api-dataexplorer.unescap.org/rest'
MAX_BYTES = 10000000

def _get(path):
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', str(MAX_BYTES), BASE + path], capture_output=True, timeout=35)
    if r.returncode:
        raise RuntimeError('ESCAP request failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > MAX_BYTES:
        raise ValueError('ESCAP response too large')
    return r.stdout.decode('utf-8-sig')

def _token(v, label, pattern='[A-Za-z0-9_]{1,100}'):
    if not isinstance(v, str) or not re.fullmatch(pattern, v):
        raise ValueError('invalid ' + label)
    return v

def dataflows():
    root = ET.fromstring(_get('/dataflow'))
    out = []
    for x in root.iter():
        if x.tag.split('}')[-1] != 'Dataflow':
            continue
        item = {'id': x.get('id'), 'agency': x.get('agencyID'), 'version': x.get('version')}
        item['name'] = next((y.text for y in x if y.tag.split('}')[-1] == 'Name'), '')
        item['structure'] = next((y.attrib for y in x.iter() if y.tag.split('}')[-1] == 'Ref'), None)
        item['annotations'] = [ET.tostring(y, encoding='unicode') for y in x.iter() if y.tag.split('}')[-1] == 'Annotation']
        out.append(item)
    return {'source': BASE + '/dataflow', 'dataflows': out}

def structure(agency, structure_id, version):
    agency = _token(agency, 'agency')
    structure_id = _token(structure_id, 'structure')
    version = _token(version, 'version', '[0-9]+(?:\\.[0-9]+)*')
    path = '/datastructure/' + agency + '/' + structure_id + '/' + version + '?references=children'
    xml = _get(path)
    ET.fromstring(xml)
    return {'source': BASE + path, 'sdmx_xml': xml, 'note': 'Original structure with referenced codelists and dimension order.'}

def series(agency, flow, version, key, start, end):
    agency = _token(agency, 'agency')
    flow = _token(flow, 'flow')
    version = _token(version, 'version', '[0-9]+(?:\\.[0-9]+)*')
    key = _token(key, 'key', '[A-Za-z0-9_+.-]{1,200}')
    if any((isinstance(x, bool) or not isinstance(x, int) or (not 1800 <= x <= 2100) for x in (start, end))) or start > end:
        raise ValueError('invalid years')
    path = '/data/' + agency + ',' + flow + ',' + version + '/' + key + '?' + urlencode({'startPeriod': start, 'endPeriod': end, 'format': 'csv'})
    raw = _get(path)
    if raw.lstrip().startswith('<'):
        raise RuntimeError('ESCAP returned XML instead of CSV: ' + raw[:300])
    reader = csv.DictReader(io.StringIO(raw))
    if not reader.fieldnames or not {'DATAFLOW', 'TIME_PERIOD', 'OBS_VALUE'}.issubset(reader.fieldnames):
        raise ValueError('unexpected ESCAP response')
    return {'source': BASE + path, 'observations': list(reader), 'note': 'Codes, units and dimension order are defined by the dataflow structure; source qualifiers are retained. The tested flows are marked NonProductionDataflow in the official catalog; verify status before use.'}
