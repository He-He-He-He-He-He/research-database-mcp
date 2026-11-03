"""IMF FAS ATM count and density via World Bank Data360."""
import release_runtime
import argparse, json, re, requests
BASE = 'https://data360api.worldbank.org/data360/data'
INDICATOR = 'IMF_FAS_FA18'
UNITS = ('ATM', '10P5AD', '10P3KM2')

def query(country, start, end, unit='ATM'):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country) or (not 2000 <= start <= end <= 2100) or (unit not in UNITS):
        raise ValueError('invalid query')
    p = {'DATABASE_ID': 'IMF_FAS', 'INDICATOR': INDICATOR, 'REF_AREA': country, 'timePeriodFrom': start, 'timePeriodTo': end}
    r = requests.get(BASE, params=p, timeout=40)
    r.raise_for_status()
    j = r.json()
    allrows = j.get('value')
    if not isinstance(allrows, list) or not isinstance(j.get('count'), int) or j['count'] != len(allrows):
        raise ValueError('incomplete response')
    if any((x.get('DATABASE_ID') != 'IMF_FAS' or x.get('INDICATOR') != INDICATOR or x.get('REF_AREA') != country or (x.get('FREQ') != 'A') for x in allrows)):
        raise ValueError('unexpected dimensions')
    rows = [x for x in allrows if x.get('UNIT_MEASURE') == unit and x.get('UNIT_MULT') == 0]
    years = [x.get('TIME_PERIOD') for x in rows]
    if len(set(years)) != len(years):
        raise ValueError('multiple unidentified series for same year and unit')
    return {'source': r.url, 'metadata_url': 'https://data360files.worldbank.org/data360-data/metadata/IMF_FAS/IMF_FAS_FA18.pdf', 'provider': 'IMF Financial Access Survey via World Bank Data360', 'unit': unit, 'matched_count': len(rows), 'records': rows, 'note': 'ATM=count; 10P5AD=per 100,000 adults; 10P3KM2=per 1,000 square km. Missing is not zero.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    p.add_argument('--unit', choices=UNITS, default='ATM')
    a = p.parse_args()
    print(json.dumps(query(a.country, a.start, a.end, a.unit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
