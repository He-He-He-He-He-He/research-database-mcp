"""IMF COFER global allocated foreign-exchange reserve currency shares."""
import release_runtime
import argparse, json, re, requests
BASE = 'https://api.imf.org/external/sdmx/3.0/data/dataflow/IMF.STA/COFER/+/'
CURRENCIES = ('USD', 'EUR', 'CNY', 'JPY', 'GBP', 'AUD', 'CAD', 'CHF', 'OTHC')

def query(currency, start='2025-Q1', end='2026-Q2'):
    pattern = '\\d{4}-Q[1-4]'
    if currency not in CURRENCIES or not isinstance(start, str) or (not isinstance(end, str)) or (not re.fullmatch(pattern, start)) or (not re.fullmatch(pattern, end)) or (start > end):
        raise ValueError('invalid query')
    url = BASE + 'G001.AFXRA.CI_' + currency + '.SHRO_PT.Q'
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
    series_dims = dims['series']
    expected = {'COUNTRY': 'G001', 'INDICATOR': 'AFXRA', 'FXR_CURRENCY': 'CI_' + currency, 'TYPE_OF_TRANSFORMATION': 'SHRO_PT', 'FREQUENCY': 'Q'}
    if {x['id']: x['values'][0]['id'] for x in series_dims if len(x.get('values', [])) == 1} != expected:
        raise ValueError('unexpected dimensions')
    obs_dims = dims['observation']
    if len(obs_dims) != 1 or obs_dims[0]['id'] != 'TIME_PERIOD':
        raise ValueError('unexpected time dimension')
    times = obs_dims[0]['values']
    series = datasets[0].get('series', {})
    if len(series) != 1:
        raise ValueError('unexpected number of series')
    out = []
    for ix, record in next(iter(series.values()))['observations'].items():
        if not ix.isdigit() or int(ix) >= len(times):
            raise ValueError('unexpected observation index')
        period = times[int(ix)].get('value')
        if period and start <= period <= end:
            out.append({'quarter': period, 'value_percent': record[0], 'raw_observation': record})
    return {'source': r.url, 'provider': 'IMF COFER', 'currency': currency, 'denominator': 'world COFER currency-attributed reserves, including imputed estimates in revised series', 'records': out, 'note': 'Since the 2025Q3 release the IMF imputes missing currency allocations with revisions to 2000Q1; check the historical coverage and revisions. Changes may reflect exchange-rate valuation as well as flows.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('currency', choices=CURRENCIES)
    p.add_argument('--start', default='2025-Q1')
    p.add_argument('--end', default='2026-Q2')
    a = p.parse_args()
    print(json.dumps(query(a.currency, a.start, a.end), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
