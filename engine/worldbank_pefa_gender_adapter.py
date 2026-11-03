"""World Bank PEFA gender-responsive public financial management public assessments."""
import release_runtime
import argparse, json, re, requests
BASE = 'https://api.worldbank.org/v2/sources/79/'

def _get(path, page=1):
    r = requests.get(BASE + path, params={'format': 'json', 'per_page': 500, 'page': page}, timeout=45)
    r.raise_for_status()
    try:
        j = r.json()
    except ValueError:
        raise ValueError('World Bank returned non-JSON or unavailable data')
    if not isinstance(j, dict):
        raise ValueError('unexpected response')
    return (j, r.url)

def catalog(kind, keyword='', page=1):
    if kind not in ('series', 'country') or not isinstance(keyword, str) or len(keyword) > 100 or (not 1 <= page <= 100):
        raise ValueError('invalid query')
    j, u = _get(kind, page)
    a = j['source'][0]['concept'][0]['variable']
    a = [x for x in a if keyword.casefold() in (x['id'] + ' ' + x['value']).casefold()]
    return {'source': u, 'page': j['page'], 'pages': j['pages'], 'matched_on_page': len(a), 'records': a, 'note': 'Keyword filters current page only.'}

def observations(country, indicator):
    if not isinstance(country, str) or not re.fullmatch('[A-Z0-9.]{3,30}', country) or (not isinstance(indicator, str)) or (not re.fullmatch('GRPFM-[0-9.]{1,12}', indicator)):
        raise ValueError('invalid country or indicator')
    j, u = _get(f'country/{country}/classification/PUB/series/{indicator}/time/all')
    s = j.get('source', {})
    if s.get('id') != '79' or j.get('pages') != 1 or (not isinstance(s.get('data'), list)):
        raise ValueError('unexpected or paginated response')
    rows = []
    for x in s['data']:
        if x['value'] is None:
            continue
        dims = {d['concept']: {'code': d['id'], 'name': d['value']} for d in x['variable']}
        rows.append({'value': x['value'], 'dimensions': dims})
    return {'source': u, 'last_updated': j.get('lastupdated'), 'records': rows, 'note': 'Raw numeric assessment codes only; do not infer grade mapping without official scoring documentation. Time is assessment month, not annual observation.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    c = s.add_parser('catalog')
    c.add_argument('kind', choices=['series', 'country'])
    c.add_argument('--keyword', default='')
    c.add_argument('--page', type=int, default=1)
    q = s.add_parser('data')
    q.add_argument('country')
    q.add_argument('indicator')
    a = p.parse_args()
    v = catalog(a.kind, a.keyword, a.page) if a.cmd == 'catalog' else observations(a.country, a.indicator)
    print(json.dumps(v, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
