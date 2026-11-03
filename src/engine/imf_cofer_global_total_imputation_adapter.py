"""IMF COFER world reserves total and imputed fraction."""
import release_runtime
import argparse, json, re, requests
BASE = 'https://api.imf.org/external/sdmx/3.0/data/dataflow/IMF.STA/COFER/+/'
INDICATORS = {'total': ('TFXRA', 'NV_USD'), 'imputed_share': ('TFXRA_IMP', 'SHRO_PT')}

def query(kind, start='2025-Q3', end='2026-Q2'):
    pat = '\\d{4}-Q[1-4]'
    if kind not in INDICATORS or not isinstance(start, str) or (not isinstance(end, str)) or (not re.fullmatch(pat, start)) or (not re.fullmatch(pat, end)) or (start > end):
        raise ValueError('invalid query')
    indicator, transform = INDICATORS[kind]
    url = BASE + 'G001.' + indicator + '.CI_T.' + transform + '.Q'
    r = requests.get(url, timeout=45)
    r.raise_for_status()
    if len(r.content) > 2000000:
        raise ValueError('unexpected response size')
    d = r.json().get('data', {})
    structures = d.get('structures', [])
    datasets = d.get('dataSets', [])
    if len(structures) != 1 or len(datasets) != 1:
        raise ValueError('unexpected SDMX structure')
    dims = structures[0]['dimensions']
    expected = {'COUNTRY': 'G001', 'INDICATOR': indicator, 'FXR_CURRENCY': 'CI_T', 'TYPE_OF_TRANSFORMATION': transform, 'FREQUENCY': 'Q'}
    if {x['id']: x['values'][0]['id'] for x in dims['series'] if len(x.get('values', [])) == 1} != expected:
        raise ValueError('unexpected dimensions')
    obs = dims['observation']
    series = datasets[0].get('series', {})
    if len(obs) != 1 or obs[0]['id'] != 'TIME_PERIOD' or len(series) != 1:
        raise ValueError('unexpected data')
    times = obs[0]['values']
    out = []
    for ix, record in next(iter(series.values()))['observations'].items():
        if not ix.isdigit() or int(ix) >= len(times):
            raise ValueError('unexpected observation index')
        period = times[int(ix)].get('value')
        if period and start <= period <= end:
            out.append({'quarter': period, 'value': record[0], 'raw_observation': record})
    return {'source': r.url, 'provider': 'IMF COFER', 'kind': kind, 'unit': 'US dollars' if kind == 'total' else 'percent of total reserves', 'records': out, 'note': 'Since the 2025Q3 release the IMF imputes missing currency composition and revises history back to 2000Q1. FX valuation and coverage affect values.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('kind', choices=INDICATORS)
    p.add_argument('--start', default='2025-Q3')
    p.add_argument('--end', default='2026-Q2')
    a = p.parse_args()
    print(json.dumps(query(a.kind, a.start, a.end), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
