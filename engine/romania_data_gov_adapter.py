"""Romania government CKAN catalog and bounded government-hosted CSV preview."""
import release_runtime
import argparse, csv, io, json, re, subprocess
from urllib.parse import urlencode, urlsplit
BASE = 'https://data.gov.ro/api/3/action/'
MAX = 5000000

def _request(url):
    p = release_runtime.run(['/usr/bin/curl', '-q', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', str(MAX), url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('Romanian open data request failed: curl ' + str(p.returncode))
    if len(p.stdout) > MAX:
        raise ValueError('response exceeds 5 MB')
    return p.stdout

def _call(action, params):
    u = BASE + action + '?' + urlencode(params)
    j = json.loads(_request(u))
    if not isinstance(j, dict) or j.get('success') is not True:
        raise ValueError('unexpected CKAN response')
    return {'source': u, 'result': j['result']}

def search(query, limit=10, offset=0):
    if not isinstance(query, str) or len(query) > 120 or (not query.strip()):
        raise ValueError('invalid query')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 50 or (not 0 <= offset <= 10000):
        raise ValueError('invalid pagination')
    return _call('package_search', {'q': query, 'rows': limit, 'start': offset})

def resource(resource_id):
    if not isinstance(resource_id, str) or not re.fullmatch('[0-9a-fA-F-]{36}', resource_id):
        raise ValueError('invalid resource id')
    return _call('resource_show', {'id': resource_id})

def csv_preview(resource_id, limit=20, encoding='utf-8-sig'):
    if encoding not in ('utf-8-sig', 'cp1250', 'cp1252'):
        raise ValueError('unsupported encoding')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('limit must be 1..100')
    r = resource(resource_id)['result']
    u = r.get('url', '')
    parsed = urlsplit(u)
    if parsed.scheme != 'https' or parsed.hostname != 'data.gov.ro' or parsed.username or parsed.password or (parsed.port not in (None, 443)):
        raise ValueError('only HTTPS CSV resources hosted by data.gov.ro are supported')
    if str(r.get('format', '')).lower().lstrip('.') != 'csv':
        raise ValueError('resource is not marked CSV')
    raw = _request(u)
    try:
        content = raw.decode(encoding)
    except UnicodeDecodeError:
        raise ValueError('CSV encoding is not UTF-8; consult resource metadata') from None
    reader = csv.reader(io.StringIO(content))
    rows = []
    for row in reader:
        rows.append(row)
        if len(rows) >= limit:
            break
    return {'source': u, 'resource': r, 'encoding': encoding, 'rows': rows, 'note': 'Raw CSV rows, not normalized. Check publisher, encoding, hierarchy, unit, period, notes and licence. Result may be only a preview; CSV source may be old.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    x = s.add_parser('search')
    x.add_argument('query')
    x.add_argument('--limit', type=int, default=10)
    x.add_argument('--offset', type=int, default=0)
    x = s.add_parser('resource')
    x.add_argument('id')
    x = s.add_parser('csv')
    x.add_argument('id')
    x.add_argument('--limit', type=int, default=20)
    x.add_argument('--encoding', choices=['utf-8-sig', 'cp1250', 'cp1252'], default='utf-8-sig')
    a = p.parse_args()
    try:
        print(json.dumps(search(a.query, a.limit, a.offset) if a.cmd == 'search' else resource(a.id) if a.cmd == 'resource' else csv_preview(a.id, a.limit, a.encoding), ensure_ascii=False, indent=2))
    except (ValueError, RuntimeError) as e:
        p.exit(1, str(e) + '\n')
if __name__ == '__main__':
    main()
