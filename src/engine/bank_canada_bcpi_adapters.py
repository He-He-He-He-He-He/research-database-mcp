"""Bank of Canada monthly commodity price index and sector components."""
import release_runtime
import argparse
import json
import subprocess
from urllib.parse import urlencode
BASE = 'https://www.bankofcanada.ca/valet/observations/group/BCPI_MONTHLY/json'

def commodity_prices(year):
    if isinstance(year, bool) or not isinstance(year, int) or (not 1972 <= year <= 2100):
        raise ValueError('year must be an integer between 1972 and 2100')
    url = BASE + '?' + urlencode({'start_date': f'{year}-01-01', 'end_date': f'{year}-12-31'})
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '25', url], capture_output=True, text=True, check=True)
    data = json.loads(r.stdout)
    rows, details = (data.get('observations'), data.get('seriesDetail'))
    if not isinstance(rows, list) or not isinstance(details, dict) or 'M.BCPI' not in details:
        raise ValueError('unexpected Bank of Canada response')
    if any((not isinstance(x, dict) or not str(x.get('d', '')).startswith(f'{year}-') for x in rows)):
        raise ValueError('observation outside requested year')
    return {'source': 'Bank of Canada Valet API', 'dataset': 'BCPI_MONTHLY', 'year': year, 'description': data.get('groupDetail'), 'series': details, 'observations': rows, 'terms': data.get('terms'), 'source_url': url, 'note': 'Chain Fisher index of prices in US dollars of Canadian-produced commodities. Monthly values may be revised as underlying data arrive; index values are not dollar prices.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('year', type=int)
    print(json.dumps(commodity_prices(p.parse_args().year), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
