"""IMF Financial Access Survey mobile transaction count indicators via Data360."""
import release_runtime
import argparse, json, re, requests
BASE = 'https://data360api.worldbank.org/data360/data'
INDICATORS = {'bank_transactions': 'IMF_FAS_FA35_COMBANK', 'mobile_money_per_account': 'IMF_FAS_FA1'}

def query(kind, country, start, end):
    if kind not in INDICATORS or not isinstance(country, str) or (not re.fullmatch('[A-Z]{3}', country)) or (not 2000 <= start <= end <= 2100):
        raise ValueError('invalid query')
    p = {'DATABASE_ID': 'IMF_FAS', 'INDICATOR': INDICATORS[kind], 'REF_AREA': country, 'timePeriodFrom': start, 'timePeriodTo': end}
    r = requests.get(BASE, params=p, timeout=40)
    r.raise_for_status()
    j = r.json()
    rows = j.get('value')
    if not isinstance(rows, list) or not isinstance(j.get('count'), int) or j['count'] != len(rows):
        raise ValueError('incomplete response')
    if any((x.get('DATABASE_ID') != 'IMF_FAS' or x.get('INDICATOR') != INDICATORS[kind] or x.get('REF_AREA') != country or (x.get('UNIT_MEASURE') != 'TRANSACT') or (x.get('UNIT_MULT') != 0) or (x.get('FREQ') != 'A') for x in rows)):
        raise ValueError('unexpected dimensions or units')
    years = [x.get('TIME_PERIOD') for x in rows]
    if len(set(years)) != len(years):
        raise ValueError('multiple unidentified series for one year')
    return {'source': r.url, 'metadata_url': 'https://data360files.worldbank.org/data360-data/metadata/IMF_FAS/' + INDICATORS[kind] + '.pdf', 'provider': 'IMF Financial Access Survey via World Bank Data360', 'kind': kind, 'records': rows, 'note': 'Counts and transactions per account are distinct measures; check metadata and original survey coverage.'}

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
