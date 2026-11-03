"""World Bank historical Subnational Malnutrition Database (source 5)."""
import release_runtime
import argparse, json, re, requests
BASE = 'https://api.worldbank.org/v2/sources/5'
CATALOG = 'https://datacatalog.worldbank.org/search/dataset/0040514/subnational-malnutrition-database'

def get(path, per_page=100):
    r = requests.get(BASE + path, params={'format': 'json', 'per_page': per_page}, timeout=35)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, dict) or 'source' not in j:
        raise ValueError('unexpected API response: ' + str(j)[:250])
    return j

def regions(text=''):
    j = get('/admin%20region', 3000)
    if int(j['pages']) != 1:
        raise ValueError('region catalog exceeds bounded page')
    entries = j['source'][0]['concept'][0]['variable']
    return {'catalog': CATALOG, 'total': j['total'], 'query': text, 'records': [x for x in entries if text.casefold() in x['value'].casefold() or text.casefold() in x['id'].casefold()]}

def indicators():
    j = get('/series', 100)
    return {'catalog': CATALOG, 'records': j['source'][0]['concept'][0]['variable']}

def query(region, indicator):
    if not re.fullmatch('[A-Za-z0-9_.-]{1,120}', region) or not re.fullmatch('[A-Za-z0-9_.-]{1,120}', indicator):
        raise ValueError('invalid region or indicator')
    j = get('/series/' + indicator + '/admin%20region/' + region + '/time/all', 100)
    if int(j['pages']) > 1:
        raise ValueError('result exceeds bounded page')
    rows = [x for x in j['source']['data'] if x['value'] is not None]
    return {'catalog': CATALOG, 'lastupdated': j.get('lastupdated'), 'region_id': region, 'indicator_id': indicator, 'records': rows, 'note': 'Historical estimates (% children under age 5); regional definitions and survey years differ. Catalog lists 1969–2014 but its description says data through 2012; this discrepancy is unresolved. Source last updated 2016-03-21.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='action', required=True)
    a = s.add_parser('regions')
    a.add_argument('text', nargs='?', default='')
    s.add_parser('indicators')
    a = s.add_parser('query')
    a.add_argument('region')
    a.add_argument('indicator')
    a = p.parse_args()
    v = regions(a.text) if a.action == 'regions' else indicators() if a.action == 'indicators' else query(a.region, a.indicator)
    print(json.dumps(v, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
