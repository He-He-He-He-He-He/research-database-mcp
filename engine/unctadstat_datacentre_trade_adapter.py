"""UN Trade and Development public data centre catalogue and annual goods trade."""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode, quote
ROOT = 'https://unctadstat-api.unctad.org'
PAGE = 'https://unctadstat.unctad.org/datacentre/'
REPORT = 'US.TradeMerchTotal'
LIMIT = 10000000

def _get(path, params=None):
    url = ROOT + path + ('?' + urlencode(params) if params else '')
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '40', '--max-filesize', str(LIMIT), url], capture_output=True, timeout=45)
    if r.returncode:
        raise RuntimeError('UNCTAD request failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > LIMIT:
        raise ValueError('response too large')
    return (url, json.loads(r.stdout))

def _reports():
    _, tree = _get('/api/datacenter')
    if not isinstance(tree, list):
        raise ValueError('unexpected catalogue')
    found = []

    def walk(nodes):
        for f in nodes:
            if not isinstance(f, dict):
                raise ValueError('unexpected catalogue folder')
            found.extend(f.get('reports', []))
            walk(f.get('subFolders', []))
    walk(tree)
    if any((not isinstance(r, dict) for r in found)):
        raise ValueError('unexpected report')
    return found

def catalog(keyword='', limit=20, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 120:
        raise ValueError('invalid keyword')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or offset < 0:
        raise ValueError('invalid pagination')
    rows = [r for r in _reports() if keyword.casefold() in str(r.get('title', '')).casefold()]
    return {'source': ROOT + '/api/datacenter', 'page': PAGE, 'matched': len(rows), 'limit': limit, 'offset': offset, 'rows': rows[offset:offset + limit], 'note': 'Catalogue describes UNCTAD compiled datasets, not independent observations. Sources and release dates vary; consult each report.'}

def merchandise(economy, year, limit=20, offset=0):
    if not isinstance(economy, str) or not re.fullmatch('[0-9]{1,4}', economy):
        raise ValueError('economy must be UNCTAD code')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1900 <= year <= 2100):
        raise ValueError('invalid year')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or offset < 0:
        raise ValueError('invalid pagination')
    hits = [r for r in _reports() if r.get('name') == REPORT]
    if len(hits) != 1 or not isinstance(hits[0].get('version'), int):
        raise ValueError('cannot resolve report version')
    version = hits[0]['version']
    _, meta = _get('/api/datacenter/reports/' + REPORT + '/info/' + str(version))
    params = {'$filter': f"Year eq {year} and Economy/Code eq '{economy}'", '$count': 'true', '$top': limit, '$skip': offset, 'culture': 'en'}
    url, result = _get('/datamart-api/' + REPORT + '/' + str(version) + '/Facts', params)
    if not isinstance(result, dict) or not isinstance(result.get('value'), list) or (not isinstance(result.get('@odata.count'), int)):
        raise ValueError('unexpected facts response')
    for r in result['value']:
        if r.get('Year') != year or r.get('Economy', {}).get('Code') != economy:
            raise ValueError('out-of-filter data')
    return {'source': url, 'page': PAGE, 'version': version, 'report_last_updated': hits[0].get('lastUpdatedDate'), 'total': result['@odata.count'], 'offset': offset, 'rows': result['value'], 'report_metadata': meta, 'note': 'UNCTAD annual merchandise trade compiled from multiple sources. M0100 is US dollars at current prices per report measures; M4023 growth and M5011 world share use different units. Preserve flow, footnotes and missing-value codes; country and global totals overlap.'}
