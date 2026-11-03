"""World Bank IDS multidimensional API, including debtor-creditor area."""
import release_runtime
import argparse, json, re, requests
BASE = 'https://api.worldbank.org/v2/sources/6/'

def get(path):
    r = requests.get(BASE + path, params={'format': 'json', 'per_page': 1000}, timeout=40)
    r.raise_for_status()
    try:
        j = r.json()
    except ValueError:
        raise ValueError('World Bank returned non-JSON, likely invalid or unavailable dimension')
    if not isinstance(j, dict) or j.get('pages', 0) > 1:
        raise ValueError('unexpected or paginated World Bank response')
    return (j, r.url)

def catalog(kind, keyword=''):
    if kind not in {'country', 'counterpart-area', 'series'}:
        raise ValueError('invalid dimension')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    j, u = get(kind)
    v = j['source'][0]['concept'][0]['variable']
    rows = [x for x in v if keyword.casefold() in (x['id'] + ' ' + x['value']).casefold()]
    return {'source': u, 'total': len(rows), 'records': rows}

def observations(country, indicator, creditor, start, end):
    if not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be ISO3')
    if not re.fullmatch('[A-Z0-9.]{3,60}', indicator):
        raise ValueError('invalid series')
    if not re.fullmatch('[A-Za-z0-9_-]{1,20}', creditor):
        raise ValueError('invalid counterpart')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1970 <= start <= end <= 2100:
        raise ValueError('invalid year range')
    j, u = get(f'country/{country}/series/{indicator}/counterpart-area/{creditor}/time/all')
    src = j.get('source', {})
    if not isinstance(src, dict) or src.get('id') != '6' or (not isinstance(src.get('data'), list)):
        raise ValueError('unexpected data response')
    records = []
    for x in src['data']:
        dimensions = {a['concept']: {'code': a['id'], 'name': a['value']} for a in x['variable']}
        year = int(dimensions['Time']['name'])
        if start <= year <= end:
            records.append({'year': year, 'value': x['value'], 'dimensions': dimensions})
    return {'source': u, 'provider': 'World Bank International Debt Statistics', 'last_updated': j.get('lastupdated'), 'matched_count': len(records), 'records': records, 'note': 'Null means missing, not zero; consult series metadata for units and scope.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    c = s.add_parser('catalog')
    c.add_argument('kind', choices=['country', 'counterpart-area', 'series'])
    c.add_argument('--keyword', default='')
    q = s.add_parser('data')
    q.add_argument('country')
    q.add_argument('indicator')
    q.add_argument('creditor')
    q.add_argument('start', type=int)
    q.add_argument('end', type=int)
    a = p.parse_args()
    result = catalog(a.kind, a.keyword) if a.cmd == 'catalog' else observations(a.country, a.indicator, a.creditor, a.start, a.end)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
