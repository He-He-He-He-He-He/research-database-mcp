"""FAO prevalence of undernourishment via World Bank Data360."""
import release_runtime
import argparse, json, re, requests
BASE = 'https://data360api.worldbank.org/data360/data'
INDICATOR = 'FAO_AS_4474'

def query(country, start, end):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country) or (not 1900 <= start <= end <= 2100):
        raise ValueError('invalid query')
    p = {'DATABASE_ID': 'FAO_AS', 'INDICATOR': INDICATOR, 'REF_AREA': country, 'timePeriodFrom': start, 'timePeriodTo': end}
    r = requests.get(BASE, params=p, timeout=40)
    r.raise_for_status()
    j = r.json()
    rows = j.get('value')
    if not isinstance(rows, list) or not isinstance(j.get('count'), int) or j['count'] != len(rows):
        raise ValueError('incomplete response')
    if any((x.get('DATABASE_ID') != 'FAO_AS' or x.get('INDICATOR') != INDICATOR or x.get('REF_AREA') != country or (x.get('UNIT_MEASURE') != 'PT_POP') or (x.get('UNIT_MULT') != 0) or (x.get('FREQ') != 'A') for x in rows)):
        raise ValueError('unexpected dimensions or units')
    years = [x.get('TIME_PERIOD') for x in rows]
    if len(set(years)) != len(years):
        raise ValueError('multiple unidentified series for one year')
    return {'source': r.url, 'metadata_url': 'https://data360files.worldbank.org/data360-data/metadata/FAO_AS/FAO_AS_4474.pdf', 'provider': 'FAO via World Bank Data360', 'records': rows, 'note': 'National estimates are three-year moving averages; reporting-year mapping to the three-year window is not established here. A displayed 2.5 may mean less than 2.5 percent.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    a = p.parse_args()
    print(json.dumps(query(a.country, a.start, a.end), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
