"""UN Population Division Data Portal: metadata and bounded authenticated observations."""
import release_runtime
import argparse, json, re, subprocess, requests
BASE = 'https://population.un.org/dataportalapi/api/v1'
SERVICE = 'zju-research-un-population-api'
ACCOUNT = '[removed]'
DOCS = 'https://population.un.org/dataportalapi/index.html'

def _get(path, params=None, auth=False):
    headers = {}
    if auth:
        p = release_runtime.run(['/usr/bin/security', 'find-generic-password', '-s', SERVICE, '-a', ACCOUNT, '-w'], capture_output=True, text=True, timeout=15)
        if p.returncode or not p.stdout.strip():
            raise RuntimeError('Cannot read UN Population API token from Keychain')
        headers['Authorization'] = 'Bearer ' + p.stdout.strip()
    try:
        r = requests.get(BASE + path, params=params, headers=headers, timeout=30)
        if r.status_code != 200:
            raise RuntimeError('UN Population API HTTP ' + str(r.status_code))
        result = r.json()
    except requests.RequestException as e:
        raise RuntimeError('UN Population API network request failed') from e
    return (result, r.headers.get('X-Applied-Defaults'))

def catalog(kind, keyword='', page=1):
    if kind not in ('sources', 'Indicators', 'locations', 'topics'):
        raise ValueError('invalid catalog')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('invalid page')
    j, _ = _get('/' + kind, {'pageNumber': page, 'pageSize': 100})
    if not isinstance(j, dict) or not isinstance(j.get('data'), list):
        raise ValueError('unexpected response')
    return {'source': BASE + '/' + kind, 'page': j.get('pageNumber'), 'pages': j.get('pages'), 'total': j.get('total'), 'records': [x for x in j['data'] if keyword.casefold() in json.dumps(x, ensure_ascii=False).casefold()], 'note': 'Keyword filters current page only.'}

def catalog_all(kind, keyword='', limit=100, offset=0):
    if kind not in ('sources', 'Indicators', 'locations', 'topics') or not isinstance(keyword, str) or len(keyword) > 150:
        raise ValueError('invalid catalog or keyword')
    if type(limit) is not int or not 1 <= limit <= 500 or type(offset) is not int or (not 0 <= offset <= 100000):
        raise ValueError('invalid limit or offset')
    records = []
    seen = set()
    expected_total = None
    expected_pages = None
    for page in range(1, 21):
        j, _ = _get('/' + kind, {'pageNumber': page, 'pageSize': 100})
        if not isinstance(j, dict) or type(j.get('pageNumber')) is not int or j['pageNumber'] != page or (type(j.get('pages')) is not int) or (not 1 <= j['pages'] <= 20) or (type(j.get('total')) is not int) or (j['total'] < 0) or (not isinstance(j.get('data'), list)) or (len(j['data']) > 100):
            raise ValueError('catalog pagination metadata invalid or exceeds 20 pages')
        if expected_total is None:
            expected_total = j['total']
            expected_pages = j['pages']
        if j['total'] != expected_total or j['pages'] != expected_pages:
            raise ValueError('catalog changed during pagination; retry')
        for item in j['data']:
            if not isinstance(item, dict) or type(item.get('id')) not in (int, str) or item['id'] in seen:
                raise ValueError('missing or repeated catalog identifier')
            seen.add(item['id'])
            records.append(item)
        if page == expected_pages:
            break
    else:
        raise ValueError('catalog exceeds 20 pages')
    if len(records) != expected_total:
        raise ValueError('catalog count mismatch; retry')
    matched = [x for x in records if keyword.casefold() in json.dumps(x, ensure_ascii=False).casefold()]
    return {'source': BASE + '/' + kind, 'catalog_total': expected_total, 'source_pages_fetched': expected_pages, 'matched_total': len(matched), 'offset': offset, 'limit': limit, 'next_offset': offset + limit if offset + limit < len(matched) else None, 'records': matched[offset:offset + limit], 'note': 'Fetches up to 20 source pages with count and identifier checks, then filters locally. The API does not guarantee an atomic snapshot; source ordering and data can change across requests.'}

def data(indicator, location, start, end, page=1, variants='4'):
    if any((isinstance(x, bool) or not isinstance(x, int) or x < 1 for x in (indicator, location, page))):
        raise ValueError('indicator, location and page must be positive integers')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1900 <= start <= end <= 2100:
        raise ValueError('invalid years')
    if not re.fullmatch('(?:all|[0-9]+(?:,[0-9]+)*)', variants):
        raise ValueError('invalid variants')
    path = f'/data/indicators/{indicator}/locations/{location}/start/{start}/end/{end}'
    j, default = _get(path, {'pageNumber': page, 'pageSize': 100, 'variants': variants}, auth=True)
    if not isinstance(j, dict) or not isinstance(j.get('data'), list):
        raise ValueError('unexpected response')
    return {'source': BASE + path, 'documentation': DOCS, 'indicator': indicator, 'location': location, 'variants_requested': variants, 'applied_defaults': default, 'page': j.get('pageNumber'), 'pages': j.get('pages'), 'total': j.get('total'), 'records': j['data'], 'note': 'Preserves source, categories, sex, age, model estimate/projection status and variant. Values are not interchangeable across those dimensions; check indicator metadata. Upstream pages limited to 100 records; request all pages as needed.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='action', required=True)
    q = s.add_parser('catalog')
    q.add_argument('kind', choices=['sources', 'Indicators', 'locations', 'topics'])
    q.add_argument('--keyword', default='')
    q.add_argument('--page', type=int, default=1)
    q = s.add_parser('data')
    q.add_argument('indicator', type=int)
    q.add_argument('location', type=int)
    q.add_argument('start', type=int)
    q.add_argument('end', type=int)
    q.add_argument('--page', type=int, default=1)
    q.add_argument('--variants', default='4')
    a = p.parse_args()
    v = catalog(a.kind, a.keyword, a.page) if a.action == 'catalog' else data(a.indicator, a.location, a.start, a.end, a.page, a.variants)
    print(json.dumps(v, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
