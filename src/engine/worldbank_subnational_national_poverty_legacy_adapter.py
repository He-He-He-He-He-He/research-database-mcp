"""World Bank historical source 38: poverty rate by national poverty line."""
import release_runtime
import argparse, json, re, requests
BASE = 'https://api.worldbank.org/v2/sources/38'
INDICATOR = 'SI.POV.NAHC'

def get(path, per_page=1000):
    r = requests.get(BASE + path, params={'format': 'json', 'per_page': per_page}, timeout=30)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, dict) or 'source' not in j:
        raise ValueError('unexpected World Bank response: ' + str(j)[:200])
    if int(j['pages']) > 1:
        raise ValueError('response exceeds bounded page')
    return j

def regions(text=''):
    j = get('/country')
    rows = j['source'][0]['concept'][0]['variable']
    return {'source': 'World Bank source 38, Subnational Poverty', 'total': j['total'], 'query': text, 'regions': [x for x in rows if text.casefold() in x['id'].casefold() or text.casefold() in x['value'].casefold()], 'note': 'Regional names may recur across countries; use the region code, not name alone.'}

def query(region):
    if not re.fullmatch('[A-Za-z0-9_.-]{1,100}', region):
        raise ValueError('invalid region code')
    j = get('/country/' + region + '/series/' + INDICATOR + '/time/all', 100)
    return {'source': 'World Bank source 38, Subnational Poverty', 'indicator': INDICATOR, 'region_code': region, 'last_updated': j.get('lastupdated'), 'records': [x for x in j['source']['data'] if x['value'] is not None], 'note': 'Historical rate as percentage of population under the national poverty line. National lines differ; cross-country comparisons are not directly valid. Original survey details and regional boundaries need checking; not a current rate.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='action', required=True)
    a = s.add_parser('regions')
    a.add_argument('text', nargs='?', default='')
    a = s.add_parser('query')
    a.add_argument('region')
    a = p.parse_args()
    print(json.dumps(regions(a.text) if a.action == 'regions' else query(a.region), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
