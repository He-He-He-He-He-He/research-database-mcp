"""Nauru Bureau of Statistics public SDMX dissemination service."""
import release_runtime
import csv, io, json, re
import requests
BASE = 'https://stats-sdmx-disseminate-nr.pacificdata.org/rest'
HEAD = {'Accept': 'application/vnd.sdmx.structure+json;version=2.0'}

def _get(path, params=None, headers=None):
    with requests.get(BASE + path, params=params, headers=headers, timeout=35, stream=True) as r:
        if r.status_code == 204:
            return ('', r.url)
        r.raise_for_status()
        raw = bytearray()
        for part in r.iter_content(65536):
            raw.extend(part)
            if len(raw) > 5000000:
                raise ValueError('Response exceeds size limit; narrow query')
        return (raw.decode('utf-8-sig'), r.url)

def _token(value, pattern='[A-Za-z0-9_]{1,120}'):
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        raise ValueError('Invalid SDMX token')
    return value

def flows(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('Invalid keyword')
    raw, url = _get('/dataflow', headers=HEAD)
    items = json.loads(raw)['data']['dataflows']
    q = keyword.casefold().strip()
    selected = [x for x in items if q in (str(x.get('id', '')) + ' ' + str(x.get('name', ''))).casefold()]
    return {'source': url, 'total': len(items), 'matched': len(selected), 'dataflows': selected, 'notes': ['Read the flow structure and code lists before interpreting observations; flow name is not necessarily a row filter.']}

def structure(identifier, agency='NBS', version='1.0'):
    _token(identifier)
    _token(agency)
    _token(version, '[0-9]+(?:\\.[0-9]+)*')
    raw, url = _get('/datastructure/' + agency + '/' + identifier + '/' + version, {'references': 'children'}, HEAD)
    return {'source': url, 'sdmx': json.loads(raw), 'notes': ['Retains dimension definitions, code lists, attributes and source metadata as published.']}

def data(flow, key='all', agency='NBS', version='1.0', limit=100):
    _token(flow)
    _token(agency)
    _token(version, '[0-9]+(?:\\.[0-9]+)*')
    _token(key, '[A-Za-z0-9_+.-]{1,200}')
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise ValueError('limit must be 1..1000')
    raw, url = _get('/data/' + agency + ',' + flow + ',' + version + '/' + key, {'format': 'csv'})
    if not raw:
        return {'source': url, 'total': 0, 'returned': 0, 'records': []}
    reader = csv.DictReader(io.StringIO(raw))
    required = {'DATAFLOW', 'TIME_PERIOD', 'OBS_VALUE'}
    if not reader.fieldnames or not required.issubset(reader.fieldnames):
        raise ValueError('Unexpected upstream CSV')
    rows = list(reader)
    return {'source': url, 'columns': reader.fieldnames, 'total': len(rows), 'returned': min(len(rows), limit), 'records': rows[:limit], 'notes': ['Use the data structure to decode dimension order and codes; dataflow names may not restrict all returned values.', 'Empty values, units, confidentiality status and comments are retained as strings. Do not interpret missing values as zero or guess confidentiality codes.', 'Census counts, household counts and estimates are distinct; current service data may be revised.']}
