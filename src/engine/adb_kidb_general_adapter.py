"""ADB Key Indicators Database SDMX v5: dataflows, indicators, and bounded data.

Official API: https://kidb.adb.org/api . ADB rate limit: 20 requests/minute.
Values retain source UNIT, UNIT_MULT, status, methodology, and footnotes.
Do not automatically rescale UNIT_MULT: source metadata may disagree with published units.
"""
import release_runtime
import csv
import io
import json
import re
import subprocess
import threading
import time
from urllib.parse import urlencode
BASE = 'https://kidb.adb.org'
_lock = threading.Lock()
_last = 0.0
MAX_BYTES = 8000000

def _get(path):
    global _last
    with _lock:
        delay = 3.2 - (time.monotonic() - _last)
        if delay > 0:
            time.sleep(delay)
        _last = time.monotonic()
        r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', str(MAX_BYTES), BASE + path], capture_output=True, timeout=35)
    if r.returncode:
        raise RuntimeError('ADB request failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > MAX_BYTES:
        raise ValueError('ADB response too large')
    return r.stdout.decode('utf-8')

def _code(value, name):
    if not isinstance(value, str) or not re.fullmatch('[A-Z0-9_]{1,80}', value):
        raise ValueError('invalid ' + name)
    return value

def dataflows(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('invalid keyword')
    obj = json.loads(_get('/api/v5/sdmx/structure/dataflow/all/all/+?format=sdmx-json'))
    flows = obj['data']['dataflows']
    selected = [x for x in flows if keyword.casefold() in (x.get('id', '') + ' ' + x.get('name', '')).casefold()]
    return {'source': BASE + '/api', 'total': len(flows), 'matched': len(selected), 'dataflows': selected, 'metadata': obj.get('meta', {})}

def indicators(flow, keyword=''):
    flow = _code(flow, 'dataflow')
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('invalid keyword')
    items = json.loads(_get('/api/dataflow/indicators/' + flow))
    if not isinstance(items, list):
        raise ValueError('unexpected ADB indicators response')
    selected = [x for x in items if keyword.casefold() in (str(x.get('code', '')) + ' ' + str(x.get('name', ''))).casefold()]
    return {'flow': flow, 'total': len(items), 'matched': len(selected), 'indicators': selected}

def economies(keyword=''):
    """Discover official ADB economy codes, including subnational codes."""
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('invalid keyword')
    path = '/api/v5/sdmx/structure/codelist/ADB/CL_ECONOMY_CODES/+?format=sdmx-json'
    obj = json.loads(_get(path))
    lists = [x for x in obj['data']['codelists'] if x.get('id') == 'CL_ECONOMY_CODES']
    if len(lists) != 1 or not isinstance(lists[0].get('codes'), list):
        raise ValueError('unexpected ADB economy codelist')
    codes = lists[0]['codes']
    matches = [x for x in codes if keyword.casefold() in (str(x.get('id', '')) + ' ' + str(x.get('name', ''))).casefold()]
    return {'source': BASE + path, 'total': len(codes), 'matched': len(matches), 'economies': matches, 'version': lists[0].get('version'), 'metadata': obj.get('meta', {}), 'note': 'Includes aggregate and subnational codes; the current data() adapter accepts three-character economy codes.'}

def data(flow, indicator, country, start, end):
    flow = _code(flow, 'dataflow')
    indicator = _code(indicator, 'indicator')
    country = _code(country, 'economy')
    if len(country) != 3:
        raise ValueError('economy must use the three-character ADB economy code')
    if any((isinstance(x, bool) or not isinstance(x, int) or x < 1900 or (x > 2100) for x in (start, end))) or start > end:
        raise ValueError('invalid year range')
    query_end = end + 1 if start == end else end
    path = '/api/v5/sdmx/data/ADB,' + flow + '/A.' + indicator + '.' + country + '?' + urlencode({'startPeriod': start, 'endPeriod': query_end, 'format': 'sdmx-csv'})
    raw = _get(path)
    if raw.lstrip().startswith('<'):
        raise RuntimeError('ADB returned an XML response instead of CSV: ' + raw[:500])
    reader = csv.DictReader(io.StringIO(raw))
    needed = {'DATAFLOW', 'FREQ', 'INDICATOR', 'ECONOMY_CODE', 'TIME_PERIOD', 'OBS_VALUE', 'UNIT', 'UNIT_MULT'}
    if not reader.fieldnames or not needed.issubset(reader.fieldnames):
        raise ValueError('unexpected ADB CSV columns')
    records = []
    for row in reader:
        if row['INDICATOR'] != indicator or row['ECONOMY_CODE'] != country:
            raise ValueError('unexpected ADB series')
        if not row['TIME_PERIOD'].isdigit():
            raise ValueError('unexpected period')
        if start <= int(row['TIME_PERIOD']) <= end:
            records.append(row)
    return {'source': BASE + path, 'flow': flow, 'indicator': indicator, 'economy': country, 'observations': records, 'note': 'UNIT and UNIT_MULT are source fields. Do not automatically rescale: some series have inconsistent magnitude metadata; verify units against ADB published tables and indicator metadata.'}
