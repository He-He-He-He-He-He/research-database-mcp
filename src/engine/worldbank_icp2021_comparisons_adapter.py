"""International Comparison Program 2021 cycle, World Bank source 90."""
import release_runtime
import argparse, json, re, requests
BASE = 'https://api.worldbank.org/v2/sources/90/'

def get(path):
    r = requests.get(BASE + path, params={'format': 'json', 'per_page': 1000}, timeout=40)
    r.raise_for_status()
    try:
        j = r.json()
    except ValueError:
        raise ValueError('World Bank returned non-JSON; combination may be unavailable')
    if not isinstance(j, dict) or int(j.get('pages', 0)) > 1:
        raise ValueError('unexpected or paginated response')
    return (j, r.url)

def catalog(kind, keyword=''):
    if kind not in {'country', 'series', 'classification', 'time'}:
        raise ValueError('invalid dimension')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    j, u = get(kind)
    v = j['source'][0]['concept'][0]['variable']
    rows = [x for x in v if keyword.casefold() in (x['id'] + ' ' + x['value']).casefold()]
    return {'source': u, 'matched_count': len(rows), 'records': rows}

def observations(country, product, classification, year):
    if not re.fullmatch('[A-Z0-9]{3}', country) or not re.fullmatch('[0-9]{7}', product) or (not re.fullmatch('[A-Za-z0-9.]{2,30}', classification)):
        raise ValueError('invalid country, product or classification')
    if isinstance(year, bool) or not isinstance(year, int) or (not 2017 <= year <= 2023):
        raise ValueError('year outside this release')
    j, u = get(f'country/{country}/series/{product}/classification/{classification}/time/YR{year}')
    s = j.get('source', {})
    if not isinstance(s, dict) or s.get('id') != '90' or (not isinstance(s.get('data'), list)):
        raise ValueError('unexpected data')
    out = []
    for x in s['data']:
        dims = {d['concept']: {'code': d['id'], 'name': d['value']} for d in x['variable']}
        out.append({'raw_value': x['value'], 'dimensions': dims})
    return {'source': u, 'provider': 'World Bank International Comparison Program', 'release': 'ICP 2021 cycle', 'last_updated': j.get('lastupdated'), 'records': out, 'note': 'Indicator type and units are given by Classification. PPP is not a market exchange rate; some years are extrapolations. Null is missing.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    c = s.add_parser('catalog')
    c.add_argument('kind', choices=['country', 'series', 'classification', 'time'])
    c.add_argument('--keyword', default='')
    q = s.add_parser('data')
    q.add_argument('country')
    q.add_argument('product')
    q.add_argument('classification')
    q.add_argument('year', type=int)
    a = p.parse_args()
    result = catalog(a.kind, a.keyword) if a.cmd == 'catalog' else observations(a.country, a.product, a.classification, a.year)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
