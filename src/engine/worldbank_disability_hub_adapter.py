"""World Bank Disability Data Hub source 92 indicator catalog and observations."""
import release_runtime
import argparse, json, re, requests
BASE = 'https://api.worldbank.org/v2'
ABOUT = 'https://disabilitydata.worldbank.org/en/about'

def fetch(path, **params):
    r = requests.get(BASE + path, params={'format': 'json', **params}, timeout=30)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, list) or not isinstance(j[0], dict) or 'page' not in j[0]:
        raise ValueError('World Bank API error: ' + str(j)[:300])
    return j

def search(query='', page=1, per_page=100):
    if not 1 <= page <= 20 or not 1 <= per_page <= 100:
        raise ValueError('invalid pagination')
    meta, records = fetch('/sources/92/indicators', page=page, per_page=per_page)
    return {'source': 'World Bank Disability Data Hub (source 92)', 'page': meta['page'], 'pages': meta['pages'], 'total': meta['total'], 'query': query, 'records': [{'id': x['id'], 'name': x['name']} for x in records or [] if query.casefold() in x['name'].casefold() or query.casefold() in x['id'].casefold()], 'note': 'Search filters only the requested page; inspect all pages for exhaustive matches.'}

def query(country, indicator):
    if not re.fullmatch('[A-Za-z]{3}', country) or not re.fullmatch('[A-Za-z0-9_]{1,100}', indicator):
        raise ValueError('invalid country or indicator')
    meta, defs = fetch('/sources/92/indicators/' + indicator, per_page=1)
    if not defs:
        raise ValueError('indicator not found')
    meta, rows = fetch('/country/' + country.upper() + '/indicator/' + indicator, source=92, per_page=100)
    if int(meta['pages']) > 1:
        raise ValueError('too many result pages')
    return {'source': 'World Bank Disability Data Hub (source 92)', 'indicator': defs[0], 'api_lastupdated': meta.get('lastupdated'), 'methodology': ABOUT, 'records': [x for x in rows or [] if x.get('value') is not None], 'note': 'Country survey/census years, definitions, functional difficulty levels and denominators differ by indicator; read indicator description and methodology before comparisons. Data are estimates, not current real-time measurements.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='action', required=True)
    a = s.add_parser('search')
    a.add_argument('text', nargs='?', default='')
    a.add_argument('--page', type=int, default=1)
    a = s.add_parser('query')
    a.add_argument('country')
    a.add_argument('indicator')
    a = p.parse_args()
    v = search(a.text, a.page) if a.action == 'search' else query(a.country, a.indicator)
    print(json.dumps(v, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
