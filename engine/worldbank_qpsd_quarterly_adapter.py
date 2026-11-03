"""World Bank and IMF Quarterly Public Sector Debt, source 20."""
import release_runtime
import argparse, json, re, requests
BASE = 'https://api.worldbank.org/v2/sources/20/'

def get(path):
    r = requests.get(BASE + path, params={'format': 'json', 'per_page': 1000}, timeout=40)
    r.raise_for_status()
    try:
        j = r.json()
    except ValueError:
        raise ValueError('World Bank returned non-JSON; data may be unavailable')
    if not isinstance(j, dict) or int(j.get('pages', 0)) > 1:
        raise ValueError('unexpected or paginated response')
    return (j, r.url)

def catalog(kind, keyword=''):
    if kind not in {'country', 'series'}:
        raise ValueError('invalid dimension')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    j, u = get(kind)
    v = j['source'][0]['concept'][0]['variable']
    rows = [x for x in v if keyword.casefold() in (x['id'] + ' ' + x['value']).casefold()]
    return {'source': u, 'matched_count': len(rows), 'records': rows}

def observations(country, indicator, start, end):
    if not re.fullmatch('[A-Z]{3}', country) or not re.fullmatch('[A-Z0-9.]{3,80}', indicator):
        raise ValueError('invalid country or indicator')
    if not isinstance(start, str) or not isinstance(end, str) or (not re.fullmatch('(19|20)\\d{2}Q[1-4]', start)) or (not re.fullmatch('(19|20)\\d{2}Q[1-4]', end)) or (start > end):
        raise ValueError('quarter must be YYYYQ1..YYYYQ4')
    j, u = get(f'country/{country}/series/{indicator}/time/all')
    s = j.get('source', {})
    if not isinstance(s, dict) or s.get('id') != '20' or (not isinstance(s.get('data'), list)):
        raise ValueError('unexpected data')
    out = []
    for x in s['data']:
        dims = {d['concept']: {'code': d['id'], 'name': d['value']} for d in x['variable']}
        q = dims['Time']['name']
        if start <= q <= end:
            out.append({'quarter': q, 'raw_value': x['value'], 'dimensions': dims})
    return {'source': u, 'provider': 'World Bank and IMF Quarterly Public Sector Debt', 'last_updated': j.get('lastupdated'), 'records': out, 'note': 'Respect government sector, valuation, currency, instrument, maturity and series units; missing is not zero.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    c = s.add_parser('catalog')
    c.add_argument('kind', choices=['country', 'series'])
    c.add_argument('--keyword', default='')
    q = s.add_parser('data')
    q.add_argument('country')
    q.add_argument('indicator')
    q.add_argument('start')
    q.add_argument('end')
    a = p.parse_args()
    result = catalog(a.kind, a.keyword) if a.cmd == 'catalog' else observations(a.country, a.indicator, a.start, a.end)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
