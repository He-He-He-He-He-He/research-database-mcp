"""World Bank Global Economic Monitor monthly/quarterly indicators, source 15."""
import release_runtime
import argparse, json, re, requests
BASE = 'https://api.worldbank.org/v2/sources/15/'

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
    if kind not in {'country', 'series', 'time'}:
        raise ValueError('invalid dimension')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    j, u = get(kind)
    v = j['source'][0]['concept'][0]['variable']
    out = [x for x in v if keyword.casefold() in (x['id'] + ' ' + x['value']).casefold()]
    return {'source': u, 'matched_count': len(out), 'records': out}

def metadata(indicator):
    if not re.fullmatch('[A-Z0-9_]{3,40}', indicator):
        raise ValueError('invalid indicator')
    j, u = get('series/' + indicator + '/metadata')
    v = j['source'][0]['concept'][0]['variable'][0]
    if v['id'] != indicator:
        raise ValueError('unexpected metadata')
    return {'source': u, 'indicator': indicator, 'metadata': v['metatype']}

def observation(country, indicator, period):
    if not re.fullmatch('[A-Z0-9]{3}', country) or not re.fullmatch('[A-Z0-9_]{3,40}', indicator):
        raise ValueError('invalid country or indicator')
    if not re.fullmatch('(19|20)\\d{2}(?:M(?:0[1-9]|1[0-2])|Q[1-4])?', period):
        raise ValueError('period must be YYYY, YYYYMmm or YYYYQn')
    j, u = get(f'country/{country}/series/{indicator}/time/{period}')
    s = j.get('source', {})
    if not isinstance(s, dict) or s.get('id') != '15' or (not isinstance(s.get('data'), list)):
        raise ValueError('unexpected data')
    out = []
    for x in s['data']:
        dims = {d['concept']: {'code': d['id'], 'name': d['value']} for d in x['variable']}
        out.append({'raw_value': x['value'], 'dimensions': dims})
    return {'source': u, 'provider': 'World Bank Global Economic Monitor', 'last_updated': j.get('lastupdated'), 'records': out, 'note': 'Consult both series label and metadata; some conflict. Null means missing. Figures may be based on third-party datasets.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    c = s.add_parser('catalog')
    c.add_argument('kind', choices=['country', 'series', 'time'])
    c.add_argument('--keyword', default='')
    m = s.add_parser('metadata')
    m.add_argument('indicator')
    q = s.add_parser('data')
    q.add_argument('country')
    q.add_argument('indicator')
    q.add_argument('period')
    a = p.parse_args()
    result = catalog(a.kind, a.keyword) if a.cmd == 'catalog' else metadata(a.indicator) if a.cmd == 'metadata' else observation(a.country, a.indicator, a.period)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
