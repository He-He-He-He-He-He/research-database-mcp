"""World Bank/IMF QEDS quarterly external debt, SDDS and GDDS sources."""
import release_runtime
import argparse, json, re, requests
BASE = 'https://api.worldbank.org/v2/sources/'
SOURCES = {'sdds': '22', 'gdds': '23'}

def get(source, path, page=1):
    r = requests.get(BASE + SOURCES[source] + '/' + path, params={'format': 'json', 'per_page': 1000, 'page': page}, timeout=40)
    r.raise_for_status()
    try:
        j = r.json()
    except ValueError:
        raise ValueError('World Bank returned non-JSON; dimension or data may be unavailable')
    if not isinstance(j, dict):
        raise ValueError('unexpected response')
    return (j, r.url)

def catalog(source, kind, keyword='', page=1):
    if source not in SOURCES or kind not in {'country', 'series'}:
        raise ValueError('invalid source or dimension')
    if not isinstance(keyword, str) or len(keyword) > 100 or isinstance(page, bool) or (not isinstance(page, int)) or (not 1 <= page <= 100):
        raise ValueError('invalid query')
    j, u = get(source, kind, page)
    v = j['source'][0]['concept'][0]['variable']
    rows = [x for x in v if keyword.casefold() in (x['id'] + ' ' + x['value']).casefold()]
    return {'source': u, 'page': j['page'], 'pages': j['pages'], 'total': j['total'], 'matched_on_page': len(rows), 'records': rows, 'note': 'Keyword applies only to current page.'}

def observations(source, country, indicator, start, end):
    if source not in SOURCES or not re.fullmatch('[A-Z]{3}', country) or (not re.fullmatch('[A-Z0-9.]{3,100}', indicator)):
        raise ValueError('invalid source, country or indicator')
    if not isinstance(start, str) or not isinstance(end, str) or (not re.fullmatch('(19|20)\\d{2}Q[1-4]', start)) or (not re.fullmatch('(19|20)\\d{2}Q[1-4]', end)) or (start > end):
        raise ValueError('quarter must be YYYYQ1..YYYYQ4')
    j, u = get(source, f'country/{country}/series/{indicator}/time/all')
    s = j.get('source', {})
    if int(j['pages']) != 1 or not isinstance(s, dict) or s.get('id') != SOURCES[source] or (not isinstance(s.get('data'), list)):
        raise ValueError('unexpected data')
    out = []
    for x in s['data']:
        dims = {d['concept']: {'code': d['id'], 'name': d['value']} for d in x['variable']}
        quarter = dims['Time']['name']
        if start <= quarter <= end:
            out.append({'quarter': quarter, 'raw_value': x['value'], 'dimensions': dims})
    return {'source': u, 'provider': 'World Bank and IMF Quarterly External Debt Statistics', 'database': source, 'last_updated': j.get('lastupdated'), 'records': out, 'note': 'Check sectors, maturity, instruments, units, and reporting country. Null means missing, not zero.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    c = s.add_parser('catalog')
    c.add_argument('source', choices=SOURCES)
    c.add_argument('kind', choices=['country', 'series'])
    c.add_argument('--keyword', default='')
    c.add_argument('--page', type=int, default=1)
    q = s.add_parser('data')
    q.add_argument('source', choices=SOURCES)
    q.add_argument('country')
    q.add_argument('indicator')
    q.add_argument('start')
    q.add_argument('end')
    a = p.parse_args()
    result = catalog(a.source, a.kind, a.keyword, a.page) if a.cmd == 'catalog' else observations(a.source, a.country, a.indicator, a.start, a.end)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
