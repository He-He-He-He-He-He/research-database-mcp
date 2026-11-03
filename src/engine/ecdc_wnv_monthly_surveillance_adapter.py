"""ECDC/EFSA monthly West Nile virus surveillance report, Table 1 CSV."""
import release_runtime
import base64
import csv
import io
import re
import subprocess
URL = 'https://wnv-monthly.ecdc.europa.eu/'
MAX_BYTES = 35000000

def _load():
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '90', '--max-filesize', str(MAX_BYTES), URL], capture_output=True, timeout=95)
    if r.returncode:
        raise RuntimeError('ECDC request failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > MAX_BYTES:
        raise ValueError('report too large')
    s = r.stdout.decode('utf-8')
    match = re.search('data:text/csv;base64,([A-Za-z0-9+/=]+)', s)
    if not match:
        raise ValueError('Table 1 CSV not found')
    csvtext = base64.b64decode(match.group(1), validate=True).decode('utf-8-sig')
    rows = list(csv.DictReader(io.StringIO(csvtext, newline='')))
    required = {'Region', 'Country', 'Affected area', 'NUTS or GAUL code', 'Number of human WNV cases', 'Number of animal outbreaks'}
    if not rows or not required.issubset(rows[0]):
        raise ValueError('unexpected CSV schema')
    text = re.sub('<[^>]+>', ' ', s)
    dates = re.search('number of WNV outbreaks among equids and birds\\s+reported within Europe in\\s+(\\d{4}).{0,180}?as at\\s+(\\d{1,2}\\s+[A-Za-z]+\\s+\\d{4})', text, re.I | re.S)
    return (rows, {'season': dates.group(1), 'data_as_at': dates.group(2)} if dates else {'season': None, 'data_as_at': None})

def search(country, limit=20, offset=0):
    if not isinstance(country, str) or not country.strip() or len(country) > 120:
        raise ValueError('invalid country')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or offset < 0:
        raise ValueError('invalid pagination')
    rows, info = _load()
    chosen = [x for x in rows if x.get('Country', '').casefold() == country.casefold()]
    return {'source': URL, **info, 'country': country, 'total': len(chosen), 'limit': limit, 'offset': offset, 'rows': chosen[offset:offset + limit], 'note': 'Table 1 reports locally acquired human cases and animal outbreaks (equids and birds), by reported region; these are different measures, not population rates, deaths, all infections, or case fatality. Reported regional data and season are provisional and may change. Country filtering and pagination are local; only current web report is queried.'}
