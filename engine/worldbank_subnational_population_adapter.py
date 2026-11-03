"""World Bank source 50 historical first-level subnational population estimates."""
import release_runtime
import argparse, json, re, requests
from urllib.parse import quote
BASE = 'https://api.worldbank.org/v2/sources/50/'

def _get(path, params=None):
    p = {'format': 'json', 'per_page': 100}
    p.update(params or {})
    r = requests.get(BASE + path, params=p, timeout=45)
    r.raise_for_status()
    try:
        j = r.json()
    except ValueError:
        raise ValueError('World Bank returned non-JSON or unavailable data')
    if not isinstance(j, dict):
        raise ValueError('unexpected response')
    return (j, r.url)

def catalog(kind, keyword='', page=1):
    if kind not in ('country', 'series') or not isinstance(keyword, str) or len(keyword) > 100 or (not 1 <= page <= 100):
        raise ValueError('invalid query')
    j, u = _get(kind, {'page': page})
    a = j['source'][0]['concept'][0]['variable']
    a = [x for x in a if keyword.casefold() in (x['id'] + ' ' + x['value']).casefold()]
    return {'source': u, 'page': j['page'], 'pages': j['pages'], 'total_catalog': j['total'], 'matched_on_page': len(a), 'records': a, 'note': 'Keyword applies to returned page only.'}

def observations(area, indicator='SP.POP.TOTL', start=2000, end=2016):
    if not isinstance(area, str) or not re.fullmatch('[A-Za-z0-9_. -]{3,120}', area) or indicator not in ('SP.POP.TOTL', 'SP.POP.TOTL.ZS') or (not 1900 <= start <= end <= 2100):
        raise ValueError('invalid query')
    j, u = _get('country/' + quote(area, safe='') + '/series/' + indicator + '/time/all')
    s = j.get('source', {})
    if s.get('id') != '50' or j.get('pages') != 1 or (not isinstance(s.get('data'), list)):
        raise ValueError('unexpected or paginated response')
    out = []
    for x in s['data']:
        d = {y['concept']: {'code': y['id'], 'name': y['value']} for y in x['variable']}
        year = int(d['Time']['name'])
        if start <= year <= end:
            out.append({'year': year, 'value': x['value'], 'dimensions': d})
    return {'source': u, 'last_updated': j.get('lastupdated'), 'records': out, 'note': 'Historical World Bank modeled estimates, not raw official census counts.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    c = s.add_parser('catalog')
    c.add_argument('kind', choices=['country', 'series'])
    c.add_argument('--keyword', default='')
    c.add_argument('--page', type=int, default=1)
    q = s.add_parser('data')
    q.add_argument('area')
    q.add_argument('--indicator', choices=['SP.POP.TOTL', 'SP.POP.TOTL.ZS'], default='SP.POP.TOTL')
    q.add_argument('--start', type=int, default=2000)
    q.add_argument('--end', type=int, default=2016)
    a = p.parse_args()
    v = catalog(a.kind, a.keyword, a.page) if a.cmd == 'catalog' else observations(a.area, a.indicator, a.start, a.end)
    print(json.dumps(v, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
