"""IMF FAS household commercial-bank deposit and loan stocks as GDP share."""
import release_runtime
import argparse, json, re, requests
BASE = 'https://data360api.worldbank.org/data360/data'
INDICATORS = {'deposits': 'IMF_FAS_OUTD_COMBANK_S14', 'loans': 'IMF_FAS_OUTL_COMBANK_S14'}

def query(kind, country, start, end):
    if kind not in INDICATORS or not isinstance(country, str) or (not re.fullmatch('[A-Z]{3}', country)) or (not 2000 <= start <= end <= 2100):
        raise ValueError('invalid query')
    indicator = INDICATORS[kind]
    p = {'DATABASE_ID': 'IMF_FAS', 'INDICATOR': indicator, 'REF_AREA': country, 'timePeriodFrom': start, 'timePeriodTo': end}
    r = requests.get(BASE, params=p, timeout=40)
    r.raise_for_status()
    j = r.json()
    allrows = j.get('value')
    if not isinstance(allrows, list) or not isinstance(j.get('count'), int) or j['count'] != len(allrows):
        raise ValueError('incomplete response')
    if any((x.get('DATABASE_ID') != 'IMF_FAS' or x.get('INDICATOR') != indicator or x.get('REF_AREA') != country or (x.get('FREQ') != 'A') for x in allrows)):
        raise ValueError('unexpected dimensions')
    rows = [x for x in allrows if x.get('UNIT_MEASURE') == 'PT_GDP' and x.get('UNIT_MULT') == 0]
    years = [x.get('TIME_PERIOD') for x in rows]
    if len(set(years)) != len(years):
        raise ValueError('multiple unidentified percentage series per year')
    return {'source': r.url, 'metadata_url': 'https://data360files.worldbank.org/data360-data/metadata/IMF_FAS/' + indicator + '.pdf', 'provider': 'IMF Financial Access Survey via World Bank Data360', 'kind': kind, 'matched_count': len(rows), 'records': rows, 'note': 'Outstanding household commercial bank positions as percent of GDP, not annual flows or household shares. Other units excluded.'}

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
