"""Statistics Norway StatBank v2: metadata and bounded explicit-code data queries."""
import release_runtime
import json
import re
import subprocess
import urllib.parse
BASE = 'https://data.ssb.no/api/pxwebapi/v2/tables/'

def _table(table):
    if not isinstance(table, str) or not re.fullmatch('\\d{5}', table):
        raise ValueError('table must be a five-digit table code')
    return table

def _get(url):
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '30', url], capture_output=True, text=True, check=True)
    j = json.loads(r.stdout)
    if j.get('class') != 'dataset' or not isinstance(j.get('dimension'), dict):
        raise ValueError('unexpected StatBank response')
    return j

def metadata(table):
    return _get(BASE + _table(table) + '/metadata?lang=en')

def data(table, selections):
    """Get JSON-stat2, preserving labels, units, notes and null/status markers.

    selections maps every dimension code to a nonempty list of value codes.
    Explicitly limited to 1000 cells to avoid accidental bulk downloads.
    """
    table = _table(table)
    if not isinstance(selections, dict) or not selections:
        raise ValueError('provide dimension selections')
    count = 1
    p = {'lang': 'en', 'outputFormat': 'json-stat2'}
    for key, values in selections.items():
        if not isinstance(key, str) or not re.fullmatch('[A-Za-z][A-Za-z0-9_]{0,63}', key):
            raise ValueError('invalid dimension')
        if not isinstance(values, list) or not values or any((not isinstance(v, str) or not re.fullmatch('[A-Za-z0-9_+.-]{1,80}', v) for v in values)) or (len(values) != len(set(values))):
            raise ValueError('invalid value codes')
        count *= len(values)
        if count > 1000:
            raise ValueError('query exceeds 1000 cells')
        p[f'valueCodes[{key}]'] = ','.join(values)
    j = _get(BASE + table + '/data?' + urllib.parse.urlencode(p))
    if set(j.get('id', [])) != set(selections):
        raise ValueError('response dimensions differ from requested')
    for key, vs in selections.items():
        if set(j['dimension'][key]['category']['index']) != set(vs):
            raise ValueError('response value codes differ from requested')
    return j
