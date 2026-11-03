"""World Bank Enterprise Surveys indicators, source 13."""
import release_runtime
import argparse, json, re, requests
BASE = 'https://api.worldbank.org/v2/sources/13/'

def get(path):
    r = requests.get(BASE + path, params={'format': 'json', 'per_page': 1000}, timeout=40)
    r.raise_for_status()
    try:
        j = r.json()
    except ValueError:
        raise ValueError('World Bank returned non-JSON or unavailable data')
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

def metadata(indicator):
    if not re.fullmatch('[A-Z0-9._]{3,80}', indicator):
        raise ValueError('invalid indicator')
    j, u = get('series/' + indicator + '/metadata')
    v = j['source'][0]['concept'][0]['variable'][0]
    if v['id'] != indicator:
        raise ValueError('unexpected indicator metadata')
    return {'source': u, 'indicator': indicator, 'metadata': v['metatype']}

def observations(country, indicator, start, end):
    if not re.fullmatch('[A-Z]{3}', country) or not re.fullmatch('[A-Z0-9._]{3,80}', indicator):
        raise ValueError('invalid country or indicator')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1900 <= start <= end <= 2100:
        raise ValueError('invalid years')
    j, u = get(f'country/{country}/series/{indicator}/time/all')
    s = j.get('source', {})
    if not isinstance(s, dict) or s.get('id') != '13' or (not isinstance(s.get('data'), list)):
        raise ValueError('unexpected data')
    out = []
    for x in s['data']:
        dimensions = {d['concept']: {'code': d['id'], 'name': d['value']} for d in x['variable']}
        year = int(dimensions['Time']['name'])
        if start <= year <= end:
            out.append({'year': year, 'raw_value': x['value'], 'dimensions': dimensions})
    return {'source': u, 'provider': 'World Bank Enterprise Surveys', 'last_updated': j.get('lastupdated'), 'records': out, 'note': 'Unmodified API values. Check the indicator definition and surveyed year; null means missing.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    c = s.add_parser('catalog')
    c.add_argument('kind', choices=['country', 'series'])
    c.add_argument('--keyword', default='')
    m = s.add_parser('metadata')
    m.add_argument('indicator')
    q = s.add_parser('data')
    q.add_argument('country')
    q.add_argument('indicator')
    q.add_argument('start', type=int)
    q.add_argument('end', type=int)
    a = p.parse_args()
    result = catalog(a.kind, a.keyword) if a.cmd == 'catalog' else metadata(a.indicator) if a.cmd == 'metadata' else observations(a.country, a.indicator, a.start, a.end)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
