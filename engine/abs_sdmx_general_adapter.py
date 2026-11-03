"""Australian Bureau of Statistics SDMX public discovery and retrieval.

Series keys are dataflow-specific; inspect structure() to learn dimensions,
code lists, units and base periods. CSV preserves original observation status,
units and revisions. Data can be revised; values are not necessarily counts.
"""
import release_runtime
import csv
import io
import re
import xml.etree.ElementTree as ET
import requests
BASE = 'https://data.api.abs.gov.au/rest/'

def _id(value):
    if not isinstance(value, str) or not re.fullmatch('[A-Za-z0-9_]{1,100}', value):
        raise ValueError('invalid ABS dataflow ID')
    return value

def _get(path, params=None):
    r = requests.get(BASE + path, params=params, timeout=45)
    r.raise_for_status()
    return r.text

def dataflows(query=''):
    """Discover ABS dataflow IDs, versions and English titles."""
    root = ET.fromstring(_get('dataflow'))
    out = []
    for e in root.iter('{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure}Dataflow'):
        names = [n.text for n in e if n.tag.endswith('}Name') and n.text]
        item = {'id': e.get('id'), 'agency': e.get('agencyID'), 'version': e.get('version'), 'names': names}
        if query.casefold() in str(item).casefold():
            out.append(item)
    return out

def structure(flow):
    """Raw official SDMX XML including the referenced structure and codelists."""
    return _get('dataflow/ABS/' + _id(flow) + '/latest', {'references': 'all'})

def observations(flow, key, start, end):
    """Read CSV for a specific SDMX key and finite time range."""
    _id(flow)
    if not isinstance(key, str) or not re.fullmatch('[A-Za-z0-9_.+\\-]{1,300}', key) or key == 'all':
        raise ValueError('provide a specific SDMX key')
    if not all((isinstance(x, str) and re.fullmatch('\\d{4}(?:-Q[1-4]|-\\d{2})?', x) for x in (start, end))):
        raise ValueError('periods must be YYYY, YYYY-Qn or YYYY-MM')
    raw = _get('data/ABS,' + flow + '/' + key, {'startPeriod': start, 'endPeriod': end, 'format': 'csv'})
    reader = csv.DictReader(io.StringIO(raw))
    if not reader.fieldnames or 'OBS_VALUE' not in reader.fieldnames:
        raise ValueError('unexpected ABS response')
    return {'columns': reader.fieldnames, 'rows': list(reader)}
