"""GCC Statistical Centre public SDMX registry and latest observations.

Official registry: https://sdmx.marsa.gccstat.org/FusionRegistry/webservice/data.html
SDMX CSV may repeat column names; records are arrays paired with original columns.
"""
import release_runtime
import csv, io, json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://sdmx.marsa.gccstat.org/FusionRegistry/ws/public/sdmxapi/rest'
MAX_BYTES = 15000000

def _get(path):
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '40', '--max-filesize', str(MAX_BYTES), '--write-out', '\n%{http_code}', BASE + path], capture_output=True, timeout=45)
    if r.returncode:
        raise RuntimeError('GCCSTAT request failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    raw, status = r.stdout.rsplit(b'\n', 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('GCCSTAT response exceeds 15 MB')
    return None if status == b'204' else raw.decode('utf-8-sig')

def _token(s, name, pattern='[A-Za-z0-9_.-]{1,100}'):
    if not isinstance(s, str) or not re.fullmatch(pattern, s):
        raise ValueError('invalid ' + name)
    return s

def dataflows(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('invalid keyword')
    path = '/dataflow/all/all/latest/?format=sdmx-json'
    obj = json.loads(_get(path))
    flows = obj['data']['dataflows']
    matched = [x for x in flows if keyword.casefold() in (x.get('id', '') + ' ' + x.get('name', '')).casefold()]
    return {'source': BASE + path, 'total': len(flows), 'matched': len(matched), 'dataflows': matched}

def structure(agency, flow, version):
    agency = _token(agency, 'agency')
    flow = _token(flow, 'flow')
    version = _token(version, 'version', '[0-9]+(?:\\.[0-9]+)*')
    path = '/dataflow/' + agency + '/' + flow + '/' + version + '?references=all&format=sdmx-json'
    return {'source': BASE + path, 'sdmx': json.loads(_get(path))}

def latest(agency, flow, version, key='all'):
    agency = _token(agency, 'agency')
    flow = _token(flow, 'flow')
    version = _token(version, 'version', '[0-9]+(?:\\.[0-9]+)*')
    key = _token(key, 'key', '[A-Za-z0-9_+.-]{1,200}')
    path = '/data/' + agency + ',' + flow + ',' + version + '/' + key + '?' + urlencode({'lastNObservations': 1, 'format': 'csv'})
    raw = _get(path)
    if raw is None:
        return {'source': BASE + path, 'columns': [], 'rows': []}
    if raw.lstrip().startswith('<'):
        raise RuntimeError('GCCSTAT returned XML instead of CSV: ' + raw[:300])
    rows = list(csv.reader(io.StringIO(raw)))
    if not rows or 'TIME_PERIOD' not in rows[0] or 'OBS_VALUE' not in rows[0]:
        raise ValueError('unexpected GCCSTAT CSV')
    if any((len(x) != len(rows[0]) for x in rows[1:])):
        raise ValueError('inconsistent GCCSTAT CSV rows')
    return {'source': BASE + path, 'columns': rows[0], 'rows': rows[1:], 'note': 'Duplicate column names are retained by position. Last observation is per series, so time varies. Consult structure and source for units and scope.'}

def series(agency, flow, version, key, start, end):
    """Retrieve a bounded annual or monthly period while retaining duplicate columns."""
    agency = _token(agency, 'agency')
    flow = _token(flow, 'flow')
    version = _token(version, 'version', '[0-9]+(?:\\.[0-9]+)*')
    key = _token(key, 'key', '[A-Za-z0-9_+.-]{1,200}')
    if not isinstance(start, str) or not isinstance(end, str) or (not re.fullmatch('\\d{4}(?:-(?:0[1-9]|1[0-2]))?', start)) or (not re.fullmatch('\\d{4}(?:-(?:0[1-9]|1[0-2]))?', end)) or (len(start) != len(end)) or (start > end):
        raise ValueError('start and end must both be YYYY or YYYY-MM, in order')
    path = '/data/' + agency + ',' + flow + ',' + version + '/' + key + '?' + urlencode({'startPeriod': start, 'endPeriod': end, 'format': 'csv'})
    raw = _get(path)
    if raw is None:
        return {'source': BASE + path, 'columns': [], 'rows': [], 'notes': ['Source returned no observations; no values were inferred.']}
    if raw.lstrip().startswith('<'):
        raise RuntimeError('GCCSTAT returned XML instead of CSV: ' + raw[:300])
    rows = list(csv.reader(io.StringIO(raw)))
    if not rows or 'TIME_PERIOD' not in rows[0] or 'OBS_VALUE' not in rows[0]:
        raise ValueError('unexpected GCCSTAT CSV')
    if any((len(x) != len(rows[0]) for x in rows[1:])):
        raise ValueError('inconsistent GCCSTAT CSV rows')
    idx = rows[0].index('TIME_PERIOD')
    for row in rows[1:]:
        period = row[idx]
        if len(start) == 4:
            if not re.match('^\\d{4}', period) or not start <= period[:4] <= end:
                raise ValueError('GCCSTAT period outside requested range')
        elif not re.fullmatch('\\d{4}-(?:0[1-9]|1[0-2])', period) or not start <= period <= end:
            raise ValueError('GCCSTAT period outside requested range')
    return {'source': BASE + path, 'columns': rows[0], 'rows': rows[1:], 'notes': ['Duplicate column names are retained by position. Consult the structure for series dimensions, base year, source and unit; index is not an inflation rate.', 'Current source values can be revised; they are not a historical release snapshot.']}
