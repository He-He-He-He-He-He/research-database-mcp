"""OECD Data Explorer SDMX dataflow discovery and bounded observations.

API documentation: https://www.oecd.org/en/data/insights/data-explainers/2024/09/api.html
"""
import release_runtime
import argparse
import csv
import io
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
BASE = 'https://sdmx.oecd.org/public/rest'
MAX_BYTES = 16000000

def _get(path):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '45', '--max-filesize', str(MAX_BYTES), '--write-out', '\n%{http_code}', BASE + path], capture_output=True, timeout=50)
    if p.returncode:
        raise RuntimeError('OECD request failed: ' + p.stderr.decode('utf-8', 'replace')[:500])
    raw, status = p.stdout.rsplit(b'\n', 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('OECD response exceeds 16 MB; narrow the selection')
    return None if status == b'204' else raw.decode('utf-8-sig')

def _token(value, name, pattern='[A-Za-z0-9_.@-]{1,150}'):
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        raise ValueError('invalid ' + name)
    return value

def dataflows(keyword):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 120:
        raise ValueError('keyword required (1–120 characters)')
    path = '/dataflow/all/all/latest'
    root = ET.fromstring(_get(path))
    out = []
    total = 0
    for x in root.iter():
        if x.tag.split('}')[-1] != 'Dataflow':
            continue
        total += 1
        names = [v.text or '' for v in x if v.tag.split('}')[-1] == 'Name' and v.get('{http://www.w3.org/XML/1998/namespace}lang') == 'en']
        name = names[0] if names else ''
        ident = x.get('id', '')
        if keyword.casefold() in (ident + ' ' + name).casefold():
            annotations = [{'type': next((v.text for v in ann if v.tag.split('}')[-1] == 'AnnotationType'), None), 'text': next((v.text for v in ann if v.tag.split('}')[-1] == 'AnnotationText'), None)} for ann in x.iter() if ann.tag.split('}')[-1] == 'Annotation']
            out.append({'agency': x.get('agencyID'), 'id': ident, 'version': x.get('version'), 'name': name, 'annotations': annotations})
    return {'source': BASE + path, 'total': total, 'matched': len(out), 'dataflows': out, 'note': 'Registry may include nonproduction or external flows. Check annotations and structure before use.'}

def structure(agency, flow, version):
    agency = _token(agency, 'agency')
    flow = _token(flow, 'flow')
    version = _token(version, 'version', '[0-9]+(?:\\.[0-9]+)*')
    path = '/dataflow/' + agency + '/' + flow + '/' + version + '?references=all'
    raw = _get(path)
    if raw is None:
        raise ValueError('OECD structure not found')
    ET.fromstring(raw)
    return {'source': BASE + path, 'sdmx_xml': raw}

def data(agency, flow, version, key, start, end):
    agency = _token(agency, 'agency')
    flow = _token(flow, 'flow')
    version = _token(version, 'version', '[0-9]+(?:\\.[0-9]+)*')
    key = _token(key, 'key', '[A-Za-z0-9_+.-]{1,300}')
    if len([part for part in key.split('.') if part]) < 2:
        raise ValueError('select at least two dimensions to limit traffic')
    if any((isinstance(v, bool) or not isinstance(v, int) or (not 1800 <= v <= 2100) for v in (start, end))) or start > end or end - start > 20:
        raise ValueError('invalid year range (maximum 21 years)')
    path = '/data/' + agency + ',' + flow + ',' + version + '/' + key + '?' + urlencode({'startPeriod': start, 'endPeriod': end, 'format': 'csvfilewithlabels'})
    raw = _get(path)
    if raw is None:
        return {'source': BASE + path, 'columns': [], 'rows': []}
    if raw.lstrip().startswith('<'):
        raise ValueError('OECD returned XML instead of CSV')
    rows = list(csv.reader(io.StringIO(raw)))
    if not rows or not {'TIME_PERIOD', 'OBS_VALUE'}.issubset(rows[0]):
        raise ValueError('unexpected OECD CSV format')
    if any((len(row) != len(rows[0]) for row in rows[1:])):
        raise ValueError('inconsistent OECD CSV rows')
    return {'source': BASE + path, 'columns': rows[0], 'rows': rows[1:], 'note': 'Values and units retain OECD fields. Columns and rows are positional to preserve duplicate labels; check metadata, multiplier, status and coverage before comparison.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='command', required=True)
    x = s.add_parser('flows')
    x.add_argument('keyword')
    x = s.add_parser('structure')
    x.add_argument('agency')
    x.add_argument('flow')
    x.add_argument('version')
    x = s.add_parser('data')
    x.add_argument('agency')
    x.add_argument('flow')
    x.add_argument('version')
    x.add_argument('key')
    x.add_argument('start', type=int)
    x.add_argument('end', type=int)
    a = p.parse_args()
    result = dataflows(a.keyword) if a.command == 'flows' else structure(a.agency, a.flow, a.version) if a.command == 'structure' else data(a.agency, a.flow, a.version, a.key, a.start, a.end)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
