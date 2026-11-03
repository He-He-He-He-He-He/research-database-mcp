"""World Bank Business Ready three pillar scores via Data360."""
import release_runtime
import argparse, json, re, requests
BASE = 'https://data360api.worldbank.org/data360/data'
INDICATORS = {'operational_efficiency': 'WB_BREADY_OPEF', 'public_services': 'WB_BREADY_PUBSR', 'regulatory_framework': 'WB_BREADY_REGFR'}

def query(kind, country, start, end):
    if kind not in INDICATORS or not isinstance(country, str) or (not re.fullmatch('[A-Z]{3}', country)) or (not 2020 <= start <= end <= 2100):
        raise ValueError('invalid query')
    indicator = INDICATORS[kind]
    p = {'DATABASE_ID': 'WB_BREADY', 'INDICATOR': indicator, 'REF_AREA': country, 'timePeriodFrom': start, 'timePeriodTo': end}
    r = requests.get(BASE, params=p, timeout=40)
    r.raise_for_status()
    j = r.json()
    rows = j.get('value')
    if not isinstance(rows, list) or not isinstance(j.get('count'), int) or j['count'] != len(rows):
        raise ValueError('incomplete response')
    if any((x.get('DATABASE_ID') != 'WB_BREADY' or x.get('INDICATOR') != indicator or x.get('REF_AREA') != country or (x.get('UNIT_MEASURE') != 'SCORE') or (x.get('UNIT_MULT') != 0) or (x.get('FREQ') != 'A') for x in rows)):
        raise ValueError('unexpected dimensions or units')
    years = [x.get('TIME_PERIOD') for x in rows]
    if len(set(years)) != len(years):
        raise ValueError('multiple unidentified series per year')
    return {'source': r.url, 'metadata_url': 'https://data360files.worldbank.org/data360-data/metadata/WB_BREADY/' + indicator + '.pdf', 'provider': 'World Bank Business Ready via Data360', 'kind': kind, 'records': rows, 'note': 'Pillar score, not an overall rank or population percentage. Data360 vintage may lag Business Ready latest report.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('kind', choices=INDICATORS)
    p.add_argument('country')
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    a = p.parse_args()
    print(json.dumps(query(a.kind, a.country, a.start, a.end), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
