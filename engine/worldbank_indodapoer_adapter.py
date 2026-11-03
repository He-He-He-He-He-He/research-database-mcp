"""World Bank Indonesia Database for Policy and Economic Research historical regional indicators."""
import release_runtime
import argparse, json, re, requests
BASE = 'https://api.worldbank.org/v2/sources/45/'

def _get(path, page=1):
    r = requests.get(BASE + path, params={'format': 'json', 'per_page': 500, 'page': page}, timeout=40)
    r.raise_for_status()
    try:
        j = r.json()
    except ValueError:
        raise ValueError('World Bank returned non-JSON or unavailable data')
    if not isinstance(j, dict):
        raise ValueError('unexpected response')
    return (j, r.url)

def catalog(kind, keyword='', page=1):
    if kind not in ('series', 'provinces') or not isinstance(keyword, str) or len(keyword) > 100 or (not 1 <= page <= 100):
        raise ValueError('invalid catalog query')
    j, u = _get(kind, page)
    a = j['source'][0]['concept'][0]['variable']
    a = [x for x in a if keyword.casefold() in (x['id'] + ' ' + x['value']).casefold()]
    return {'source': u, 'page': j['page'], 'pages': j['pages'], 'dataset_total': j['total'], 'matched_on_page': len(a), 'records': a, 'note': 'Keyword applies only to this page.'}

def observations(country, indicator, start=2000, end=2021):
    if not isinstance(country, str) or not re.fullmatch('[A-Z0-9.]{3,40}', country) or (not isinstance(indicator, str)) or (not re.fullmatch('[A-Za-z0-9._]{1,80}', indicator)) or (not 1900 <= start <= end <= 2100):
        raise ValueError('invalid query')
    j, u = _get(f'provinces/{country}/series/{indicator}/time/all')
    s = j.get('source', {})
    if s.get('id') != '45' or j.get('pages') != 1 or (not isinstance(s.get('data'), list)):
        raise ValueError('unexpected or paginated data')
    out = []
    for x in s['data']:
        dims = {d['concept']: {'code': d['id'], 'name': d['value']} for d in x['variable']}
        y = int(dims['Time']['name'])
        if start <= y <= end:
            out.append({'year': y, 'value': x['value'], 'dimensions': dims})
    return {'source': u, 'last_updated': j.get('lastupdated'), 'records': out, 'note': 'Historical Indonesian subnational indicators: verify region level, indicator definitions, units and national underlying sources; missing is not zero.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    c = s.add_parser('catalog')
    c.add_argument('kind', choices=['series', 'provinces'])
    c.add_argument('--keyword', default='')
    c.add_argument('--page', type=int, default=1)
    q = s.add_parser('data')
    q.add_argument('country')
    q.add_argument('indicator')
    q.add_argument('--start', type=int, default=2000)
    q.add_argument('--end', type=int, default=2021)
    a = p.parse_args()
    v = catalog(a.kind, a.keyword, a.page) if a.cmd == 'catalog' else observations(a.country, a.indicator, a.start, a.end)
    print(json.dumps(v, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
