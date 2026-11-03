"""Public Expenditure and Financial Accountability 2016 framework, source 68."""
import release_runtime
import argparse, json, re, requests
BASE = 'https://api.worldbank.org/v2/sources/68/'

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
    if kind not in {'country', 'series', 'time', 'classification'}:
        raise ValueError('invalid dimension')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    j, u = get(kind)
    v = j['source'][0]['concept'][0]['variable']
    rows = [x for x in v if keyword.casefold() in (x['id'] + ' ' + x['value']).casefold()]
    return {'source': u, 'matched_count': len(rows), 'records': rows}

def assessments(area, indicator, start, end):
    if not re.fullmatch('[A-Z0-9.]{3,30}', area) or not re.fullmatch('[A-Z0-9.\\-]{3,30}', indicator):
        raise ValueError('invalid area or indicator code')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 2015 <= start <= end <= 2100:
        raise ValueError('invalid years')
    j, u = get(f'country/{area}/series/{indicator}/classification/PUB/time/all')
    s = j.get('source', {})
    if not isinstance(s, dict) or s.get('id') != '68' or (not isinstance(s.get('data'), list)):
        raise ValueError('unexpected data')
    out = []
    for x in s['data']:
        dims = {d['concept']: {'code': d['id'], 'name': d['value']} for d in x['variable']}
        code = dims['Time']['code']
        if not re.fullmatch('YR\\d{6}', code):
            raise ValueError('unexpected assessment date')
        year = int(code[2:6])
        if start <= year <= end:
            out.append({'assessment_date': code[2:6] + '-' + code[6:8], 'raw_score': x['value'], 'dimensions': dims})
    return {'source': u, 'provider': 'PEFA Secretariat via World Bank', 'framework': 'PEFA 2016', 'last_updated': j.get('lastupdated'), 'records': out, 'note': 'Values are converted assessment scores, not percentages; report date may differ from assessment period. Some area codes are subnational. Null means missing.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    c = s.add_parser('catalog')
    c.add_argument('kind', choices=['country', 'series', 'time', 'classification'])
    c.add_argument('--keyword', default='')
    q = s.add_parser('data')
    q.add_argument('area')
    q.add_argument('indicator')
    q.add_argument('start', type=int)
    q.add_argument('end', type=int)
    a = p.parse_args()
    result = catalog(a.kind, a.keyword) if a.cmd == 'catalog' else assessments(a.area, a.indicator, a.start, a.end)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
