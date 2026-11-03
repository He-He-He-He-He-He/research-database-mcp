"""FAO Global Forest Resources Assessment 2025 public exploration API.

Official OpenAPI: https://fra-data.fao.org/api-docs/ . Fields and units vary by
assessment table. Values may be estimates or computed; flags are preserved.
"""
import release_runtime
import json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://fra-data.fao.org'
MAX_BYTES = 10000000

def _get(path, params=None):
    url = BASE + path + ('?' + urlencode(params) if params else '')
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', str(MAX_BYTES), url], capture_output=True, timeout=35)
    if r.returncode:
        raise RuntimeError('FAO FRA API failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > MAX_BYTES:
        raise ValueError('FRA response exceeds 10 MB')
    return {'source': url, 'response': json.loads(r.stdout)}

def catalog():
    r = _get('/api-docs/swagger.json')
    p = r['response']['components']['parameters']
    return {'source': r['source'], 'assessment': p['assessmentName'], 'table_names': p['fra2025tableNames'], 'countries': p['countryIso'], 'columns': p['columns'], 'variables': p['variables']}

def data(country, table, year=None, variable=None):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be ISO3 uppercase')
    if not isinstance(table, str) or not re.fullmatch('[A-Za-z][A-Za-z0-9_]{0,100}', table):
        raise ValueError('invalid table name')
    p = [('assessmentName', 'fra'), ('countryISOs[]', country), ('tableNames[]', table)]
    if year is not None:
        if isinstance(year, bool) or not isinstance(year, int) or (not 1900 <= year <= 2100):
            raise ValueError('invalid year')
        p.append(('columns[]', str(year)))
    if variable is not None:
        if not isinstance(variable, str) or not re.fullmatch('[A-Za-z][A-Za-z0-9_]{0,100}', variable):
            raise ValueError('invalid variable')
        p.append(('variables[]', variable))
    r = _get('/api/explorer/data', p)
    if not isinstance(r['response'], dict) or 'fra' not in r['response']:
        raise ValueError('unexpected FRA data response')
    r['note'] = 'Assessment release and raw reported/computed/estimated flags retained. Units vary by table; check the source country assessment section.'
    r['assessment_page'] = 'https://fra-data.fao.org/assessments/fra/2025/' + country + '/sections/' + table + '/'
    return r
