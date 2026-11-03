"""World Bank CCKP country historical annual ERA5 temperature/precipitation."""
import release_runtime
import argparse, json, re, requests
BASE = 'https://cckpapi.worldbank.org/cckp/v1/'
SERIES = 'era5-x0.25_timeseries_pr,tas_timeseries_annual_1950-2025_mean_historical_era5_x0.25_mean'
DOCS = 'https://climateknowledgeportal.worldbank.org/download-data'
ORIGIN = 'https://datacatalog.worldbank.org/search/dataset/0065626/climate-change-knowledge-portal-observed-climate-data-era5-0-25-degree'

def query(country, start, end):
    if not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be ISO3')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1950 <= start <= end <= 2025:
        raise ValueError('year range must lie in 1950–2025')
    url = BASE + SERIES + '/' + country
    r = requests.get(url, params={'_format': 'json'}, timeout=30)
    r.raise_for_status()
    j = r.json()
    if j.get('metadata', {}).get('status') != 'success' or not isinstance(j.get('data'), dict):
        raise ValueError('unexpected CCKP response')
    out = {}
    for code, unit in [('tas', 'degrees Celsius'), ('pr', 'millimetres per year')]:
        cells = j['data'].get(code, {}).get(country, {})
        if not isinstance(cells, dict):
            raise ValueError('unexpected series')
        out[code] = {'unit': unit, 'records': [{'year': int(k[:4]), 'time_label': k, 'value': v} for k, v in sorted(cells.items()) if re.fullmatch('\\d{4}-07', k) and start <= int(k[:4]) <= end]}
    return {'provider': 'World Bank Climate Change Knowledge Portal', 'source': r.url, 'documentation': DOCS, 'collection': 'ERA5, Copernicus Climate Change Service and ECMWF', 'coverage': '1950–2025', 'geography': country, 'variables': out, 'note': 'National spatial aggregation of gridded ERA5 reanalysis, not a single station; do not splice directly with CRU data. tas is annual mean temperature; pr is annual precipitation. July in the raw label represents the annual period, not July. API returns 2025 but catalog describes coverage through 2022; metadata may lag. Data can be revised.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    a = p.parse_args()
    print(json.dumps(query(a.country, a.start, a.end), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
