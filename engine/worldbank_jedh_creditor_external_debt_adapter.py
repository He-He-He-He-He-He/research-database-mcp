"""World Bank Joint External Debt Hub creditor and market statistics, source 54."""
import release_runtime
import argparse, json, re, requests
BASE = 'https://api.worldbank.org/v2'
ABOUT = 'https://www.worldbank.org/en/programs/debt-statistics/statistics'

def _get(path, **params):
    r = requests.get(BASE + path, params={'format': 'json', **params}, timeout=30)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, list) or not j or (not isinstance(j[0], dict)) or ('page' not in j[0]):
        raise ValueError('Unexpected API response: ' + str(j)[:300])
    return j

def indicators(keyword=''):
    meta, rows = _get('/sources/54/indicators', per_page=100)
    if int(meta['pages']) > 1:
        raise ValueError('Catalog exceeds page limit')
    return {'source': 'Joint External Debt Hub via World Bank API source 54', 'total': meta['total'], 'records': [x for x in rows or [] if keyword.casefold() in (x['name'] + ' ' + x['id']).casefold()]}

def query(country, indicator, start, end):
    if not re.fullmatch('[A-Z]{3}', country) or not re.fullmatch('[A-Za-z0-9.]{1,150}', indicator):
        raise ValueError('invalid country or indicator')
    if any((isinstance(y, bool) or not isinstance(y, int) for y in (start, end))) or not 1980 <= start <= end <= 2100:
        raise ValueError('invalid year range')
    m, defs = _get('/sources/54/indicators/' + indicator, per_page=1)
    if not defs:
        raise ValueError('indicator not found')
    m, rows = _get('/country/' + country + '/indicator/' + indicator, source=54, per_page=1000)
    if int(m['pages']) > 1:
        raise ValueError('too many observations')
    return {'source': 'Joint External Debt Hub via World Bank API source 54', 'about': ABOUT, 'metadata': defs[0], 'last_updated': m.get('lastupdated'), 'records': [x for x in rows or [] if x.get('value') is not None and re.fullmatch('\\d{4}Q[1-4]', str(x.get('date', ''))) and (start <= int(x['date'][:4]) <= end)], 'note': 'Quarter-end creditor/market-source observations. API provides an empty unit for this series; its raw units/scaling must be confirmed before interpretation. Different sources and series overlap and should not be summed as debt totals.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='action', required=True)
    a = s.add_parser('indicators')
    a.add_argument('keyword', nargs='?', default='')
    a = s.add_parser('query')
    a.add_argument('country')
    a.add_argument('indicator')
    a.add_argument('start', type=int)
    a.add_argument('end', type=int)
    a = p.parse_args()
    print(json.dumps(indicators(a.keyword) if a.action == 'indicators' else query(a.country, a.indicator, a.start, a.end), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
