"""Malta NSO IRIS SDMX: structural metadata and bounded data queries."""
import release_runtime
import csv
import io
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://irisapi.nso.gov.mt/nsi_ws/rest/'

def _fetch(path, params=None, accept=None):
    url = BASE + path + ('?' + urlencode(params) if params else '')
    args = ['/usr/bin/curl', '-q', '--compressed', '-fsSL', '--max-time', '30', '--max-filesize', '8388608']
    if accept:
        args.extend(['-H', 'Accept: ' + accept])
    proc = release_runtime.run(args + [url], capture_output=True, timeout=35)
    if proc.returncode:
        raise RuntimeError('Malta NSO request failed: ' + proc.stderr.decode('utf8', 'replace').strip())
    if len(proc.stdout) > 8388608:
        raise RuntimeError('Response exceeds 8 MiB')
    return proc.stdout.decode('utf-8-sig')

def _flow(flow):
    if not isinstance(flow, str) or not re.fullmatch('[A-Za-z0-9_]+', flow):
        raise ValueError('Invalid dataflow ID')
    return flow

def catalog():
    return json.loads(_fetch('v2/structure/dataflow/MT1'))

def structure(flow):
    return json.loads(_fetch('v2/structure/dataflow/MT1/' + _flow(flow), {'references': 'all'}))

def observations(flow, start_year, end_year, key='', limit=1000):
    if isinstance(start_year, bool) or isinstance(end_year, bool) or (not isinstance(start_year, int)) or (not isinstance(end_year, int)) or (not 1800 <= start_year <= end_year <= 2200):
        raise ValueError('Provide a valid year range')
    if not isinstance(key, str) or not re.fullmatch('[A-Za-z0-9_.+\\-]*', key):
        raise ValueError('Invalid SDMX key')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 10000):
        raise ValueError('limit must be 1–10000')
    text = _fetch('data/MT1,' + _flow(flow) + ',1.0/' + key, {'startPeriod': start_year, 'endPeriod': end_year}, 'text/csv')
    rows = list(csv.DictReader(io.StringIO(text)))
    return {'source': 'Malta National Statistics Office IRIS', 'matched': len(rows), 'returned': min(limit, len(rows)), 'truncated': len(rows) > limit, 'rows': rows[:limit]}
