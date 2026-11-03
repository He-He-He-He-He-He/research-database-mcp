"""BIS public SDMX v2 dataflow discovery, structures and bounded series queries.

Reference metadata is returned intact so code definitions and units remain available.
BIS terms: https://data.bis.org/help/legal . Cite BIS and the specific dataset.
"""
import release_runtime
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
BASE = 'https://stats.bis.org/api/v2'
MAX_BYTES = 10000000

def _token(value, pattern, label):
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        raise ValueError('invalid ' + label)
    return value

def _get(path):
    result = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', str(MAX_BYTES), '--write-out', '\n%{http_code}', BASE + path], capture_output=True, timeout=35)
    if result.returncode:
        raise RuntimeError('BIS request failed: ' + result.stderr.decode('utf-8', 'replace')[:500])
    body, status = result.stdout.rsplit(b'\n', 1)
    if len(body) > MAX_BYTES:
        raise ValueError('BIS response exceeds size limit')
    return None if status == b'204' else body

def dataflows(keyword=''):
    """List all public BIS dataflows; optionally filter names and IDs."""
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('invalid keyword')
    obj = json.loads(_get('/structure/dataflow/BIS/all/latest'))
    flows = obj['data']['dataflows']
    matches = [f for f in flows if keyword.casefold() in (str(f.get('id', '')) + ' ' + str(f.get('name', ''))).casefold()]
    return {'source': BASE, 'total': len(flows), 'matched': len(matches), 'dataflows': matches, 'metadata': obj.get('meta', {})}

def structure(flow, version='latest'):
    """Return original dataflow and referenced definitions, including units and codes."""
    flow = _token(flow, '[A-Za-z0-9_]{1,80}', 'flow')
    version = _token(version, '(?:latest|[0-9]+(?:\\.[0-9]+)*)', 'version')
    body = _get('/structure/dataflow/BIS/' + flow + '/' + version + '?references=all')
    return None if body is None else json.loads(body)

def series(flow, key, start, end, version='latest'):
    """Retrieve an explicitly bounded SDMX series, preserving all source attributes."""
    flow = _token(flow, '[A-Za-z0-9_]{1,80}', 'flow')
    version = _token(version, '(?:latest|[0-9]+(?:\\.[0-9]+)*)', 'version')
    key = _token(key, '[A-Za-z0-9_+.-]{1,200}', 'series key')
    for value in (start, end):
        _token(value, '[0-9]{4}(?:-(?:[0-9]{2}|Q[1-4]|S[1-2])(?:-[0-9]{2})?)?', 'period')
    if start > end:
        raise ValueError('start must not be after end')
    if version == 'latest':
        flows = [item for item in dataflows()['dataflows'] if item.get('id') == flow]
        if len(flows) != 1 or not isinstance(flows[0].get('version'), str):
            raise ValueError('BIS dataflow not found or latest version ambiguous: ' + flow)
        version = _token(flows[0]['version'], '[0-9]+(?:\\.[0-9]+)*', 'resolved version')
    path = '/data/dataflow/BIS/' + flow + '/' + version + '/' + key + '?' + urlencode({'startPeriod': start, 'endPeriod': end})
    body = _get(path)
    if body is None:
        return {'source': BASE + path, 'datasets': []}
    root = ET.fromstring(body)
    sets = []
    for ds in root.iter():
        if ds.tag.split('}')[-1] != 'DataSet':
            continue
        entries = []
        for s in ds:
            if s.tag.split('}')[-1] == 'Series':
                entries.append({'attributes': dict(s.attrib), 'observations': [dict(o.attrib) for o in s if o.tag.split('}')[-1] == 'Obs']})
        sets.append({'attributes': dict(ds.attrib), 'series': entries})
    return {'source': BASE + path, 'datasets': sets, 'note': 'Codes, units and dimensions require the dataflow structure metadata; observations retain source status attributes.'}
