"""FAO moderate/severe food insecurity estimates via World Bank WDI."""
import release_runtime
import argparse, json, re, requests
BASE = 'https://api.worldbank.org/v2/'
INDICATORS = {'moderate_or_severe': 'SN.ITK.MSFI.ZS', 'severe': 'SN.ITK.SVFI.ZS'}

def query(kind, country, start, end):
    if kind not in INDICATORS or not isinstance(country, str) or (not re.fullmatch('[A-Z]{3}', country)) or (type(start) is not int) or (type(end) is not int) or (not 2000 <= start <= end <= 2100):
        raise ValueError('invalid query')
    indicator = INDICATORS[kind]
    url = BASE + 'country/' + country + '/indicator/' + indicator
    r = requests.get(url, params={'format': 'json', 'date': f'{start}:{end}', 'per_page': 500}, timeout=40)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, list) or len(j) != 2 or (not isinstance(j[1], list)) or (j[0].get('pages') != 1):
        raise ValueError('unexpected or paginated data')
    rows = j[1]
    if any((x.get('indicator', {}).get('id') != indicator or x.get('countryiso3code') != country or (not isinstance(x.get('date'), str)) or (not re.fullmatch('[0-9]{4}', x['date'])) or (not start <= int(x['date']) <= end) for x in rows)):
        raise ValueError('unexpected dimensions or year')
    return {'source': r.url, 'provider': 'FAO via World Bank World Development Indicators', 'indicator': indicator, 'unit': 'percent of population', 'records': rows, 'note': 'Severe category is included in moderate-or-severe; do not add them. FIES survey-based estimate; inspect original survey years and methodology; null means missing.'}

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
