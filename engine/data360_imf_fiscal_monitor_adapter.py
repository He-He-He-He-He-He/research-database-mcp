"""IMF Fiscal Monitor indicators as hosted by World Bank Data360."""
import release_runtime
import argparse, json, re, requests
BASE = 'https://data360api.worldbank.org/data360/data'
INDICATORS = {'gross_debt': 'IMF_FM_G_XWDG_G01_GDP_PT', 'revenue': 'IMF_FM_GGR_G01_GDP_PT', 'cyclically_adjusted_balance': 'IMF_FM_GGCB_G01_PGDP_PT'}

def query(kind, country, start, end):
    if kind not in INDICATORS or not isinstance(country, str) or (not re.fullmatch('[A-Z]{3}', country)) or any((isinstance(v, bool) or not isinstance(v, int) for v in (start, end))) or (not 1900 <= start <= end <= 2100):
        raise ValueError('invalid query')
    p = {'DATABASE_ID': 'IMF_FM', 'INDICATOR': INDICATORS[kind], 'REF_AREA': country, 'timePeriodFrom': start, 'timePeriodTo': end}
    r = requests.get(BASE, params=p, timeout=40)
    r.raise_for_status()
    j = r.json()
    rows = j.get('value')
    if not isinstance(rows, list) or not isinstance(j.get('count'), int) or j['count'] != len(rows):
        raise ValueError('incomplete response')
    if any((x.get('DATABASE_ID') != 'IMF_FM' or x.get('INDICATOR') != INDICATORS[kind] or x.get('REF_AREA') != country or (x.get('UNIT_MEASURE') != 'PT_GDP') or (x.get('UNIT_MULT') != 0) or (x.get('FREQ') != 'A') for x in rows)):
        raise ValueError('unexpected dimensions or units')
    years = [x.get('TIME_PERIOD') for x in rows]
    if any((not isinstance(y, str) or not re.fullmatch('[0-9]{4}', y) or (not start <= int(y) <= end) for y in years)):
        raise ValueError('response contains an unexpected year')
    if len(set(years)) != len(years):
        raise ValueError('multiple unidentified series for one year')
    return {'source': r.url, 'metadata_url': 'https://data360files.worldbank.org/data360-data/metadata/IMF_FM/' + INDICATORS[kind] + '.pdf', 'provider': 'IMF Fiscal Monitor via World Bank Data360', 'kind': kind, 'denominator': 'potential GDP' if kind == 'cyclically_adjusted_balance' else 'GDP', 'records': rows, 'note': 'Fiscal Monitor includes forecasts. Data360 vintage and actual/projection cutoff are not provided in observation rows; verify with IMF edition and fiscal-year conventions.'}

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
