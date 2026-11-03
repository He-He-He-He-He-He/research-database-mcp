"""UN OCHA Financial Tracking Service public funding flows by location and usage year."""
import release_runtime
import argparse, json, requests
BASE = 'https://api.hpc.tools'
DOCS = 'https://api.hpc.tools/docs/v1/'

def location(location_id):
    if isinstance(location_id, bool) or not isinstance(location_id, int) or location_id < 1:
        raise ValueError('location ID must be positive integer')
    r = requests.get(f'{BASE}/v2/public/location/{location_id}', params={'maxLevel': 0}, timeout=30)
    r.raise_for_status()
    j = r.json()
    x = j.get('data')
    if not isinstance(x, dict) or x.get('id') != location_id:
        raise ValueError('unexpected location response')
    return {'source': r.url, 'location': {k: x.get(k) for k in ('id', 'iso3', 'name', 'adminLevel', 'pcode')}}

def flows(location_id, year, page=1, limit=25):
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (location_id, year, page, limit))) or location_id < 1 or (not 2000 <= year <= 2100) or (not 1 <= page <= 10000) or (not 1 <= limit <= 100):
        raise ValueError('invalid parameters')
    r = requests.get(f'{BASE}/v1/public/fts/flow', params={'locationId': location_id, 'year': year, 'page': page, 'limit': limit}, timeout=35)
    r.raise_for_status()
    j = r.json()
    d = j.get('data')
    if j.get('status') != 'ok' or not isinstance(d, dict) or (not isinstance(d.get('flows'), list)):
        raise ValueError('unexpected FTS response')
    return {'provider': 'UN OCHA Financial Tracking Service', 'source': r.url, 'documentation': DOCS, 'location_id': location_id, 'usage_year': year, 'page': page, 'limit': limit, 'data': d, 'note': 'The location boundary can be source or destination; FTS categorizes incoming, internal and outgoing. Year is a usage-year filter, not necessarily transaction date; flows may span multiple years. Parent/child and internal flows can overlap. Do not add all records or page totals to infer unique funding; preserve statuses, destination objects and dates. Reporting is voluntary and incomplete and values may be revised.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='action', required=True)
    a = s.add_parser('location')
    a.add_argument('id', type=int)
    a = s.add_parser('flows')
    a.add_argument('id', type=int)
    a.add_argument('year', type=int)
    a.add_argument('--page', type=int, default=1)
    a.add_argument('--limit', type=int, default=25)
    a = p.parse_args()
    v = location(a.id) if a.action == 'location' else flows(a.id, a.year, a.page, a.limit)
    print(json.dumps(v, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
