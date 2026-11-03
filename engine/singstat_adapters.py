"""Singapore SingStat Table Builder: bounded time series and table metadata."""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://tablebuilder.singstat.gov.sg/api/table/'

def _id(table):
    if not isinstance(table, str) or not re.fullmatch('[A-Za-z][0-9]{5,8}', table):
        raise ValueError('invalid table resource ID')
    return table.upper()

def _get(path, params=None):
    url = BASE + path + ('?' + urlencode(params) if params else '')
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '25', url], capture_output=True, text=True, check=True)
    j = json.loads(r.stdout)
    if j.get('StatusCode') != 200 or not isinstance(j.get('Data'), dict):
        raise ValueError('SingStat did not return a successful response')
    return j['Data']

def metadata(table):
    path = 'metadata/' + _id(table)
    data = _get(path)
    return {**data, 'toolkit_source_url': BASE + path}

def series(table, series_no, years):
    """Read one series and selected annual periods. Preserve values and footnotes as strings."""
    table = _id(table)
    if not isinstance(series_no, str) or not re.fullmatch('[0-9]+(?:\\.[0-9]+)*', series_no):
        raise ValueError('invalid series number')
    if not isinstance(years, list) or not years or len(years) > 20 or any((not isinstance(y, str) or not re.fullmatch('[0-9]{4}', y) for y in years)) or (len(years) != len(set(years))):
        raise ValueError('years must be 1–20 distinct YYYY strings')
    data = _get('tabledata/' + table, {'seriesNoORrowNo': series_no, 'timeFilter': ','.join(years)})
    rows = data.get('row')
    if data.get('id') != table or not isinstance(rows, list) or len(rows) != 1 or (rows[0].get('seriesNo') != series_no):
        raise ValueError('response series differs from request')
    cols = rows[0].get('columns')
    if not isinstance(cols, list) or any((c.get('key') not in years for c in cols)):
        raise ValueError('response periods differ from request')
    return {**data, 'toolkit_source_url': BASE + 'tabledata/' + table + '?' + urlencode({'seriesNoORrowNo': series_no, 'timeFilter': ','.join(years)}), 'toolkit_note': 'Source fields and footnotes are preserved. Missing requested years are not zero; check row unit, population concept, coverage and revision date.'}
