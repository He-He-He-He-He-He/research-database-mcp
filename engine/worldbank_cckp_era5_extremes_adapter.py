"""World Bank CCKP ERA5 annual national spatial-average temperature extremes."""
import release_runtime
import argparse, json, re, requests
BASE = 'https://cckpapi.worldbank.org/cckp/v1/'
SERIES = 'era5-x0.25_timeseries_fd,txx,tnn_timeseries_annual_1950-2025_mean_historical_era5_x0.25_mean'
DOCS = 'https://climateknowledgeportal.worldbank.org/media/document/metatag.pdf'
DEFS = {'fd': ('Frost days: daily minimum temperature below 0°C', 'days/year'), 'txx': ('Annual maximum of daily maximum temperature', 'degrees Celsius'), 'tnn': ('Annual minimum of daily minimum temperature', 'degrees Celsius')}

def query(country, start, end):
    if not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be ISO3')
    if any((isinstance(v, bool) or not isinstance(v, int) for v in (start, end))) or not 1950 <= start <= end <= 2025:
        raise ValueError('year range must lie in 1950–2025')
    r = requests.get(BASE + SERIES + '/' + country, params={'_format': 'json'}, timeout=30)
    r.raise_for_status()
    j = r.json()
    if j.get('metadata', {}).get('status') != 'success' or not isinstance(j.get('data'), dict):
        raise ValueError('unexpected CCKP response')
    data = {}
    for code, (definition, unit) in DEFS.items():
        series = j['data'].get(code, {}).get(country, {})
        if not isinstance(series, dict):
            raise ValueError('unexpected series')
        data[code] = {'definition': definition, 'unit': unit, 'records': [{'year': int(k[:4]), 'time_label': k, 'value': v} for k, v in sorted(series.items()) if re.fullmatch('\\d{4}-07', k) and start <= int(k[:4]) <= end]}
    return {'provider': 'World Bank Climate Change Knowledge Portal', 'source': r.url, 'methodology': DOCS, 'dataset': 'ERA5 climate reanalysis annual 0.25 degree spatial averages', 'country': country, 'variables': data, 'note': 'Each value is the national spatial average of each grid cell annual index, not the single nationwide hottest/coldest station or a national synchronous frost-day count. July labels mark annual periods. ERA5 is reanalysis combining observations and models; estimates can be revised.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    a = p.parse_args()
    print(json.dumps(query(a.country, a.start, a.end), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
