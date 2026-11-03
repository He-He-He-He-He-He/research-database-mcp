"""NOAA GlobalTemp v6.1 official areal temperature anomaly time series."""
import release_runtime
import argparse, json, re, requests
BASE = 'https://www.ncei.noaa.gov/data/noaa-global-surface-temperature/v6.1/access/timeseries/'
BANDS = {'00N.30N', '00N.90N', '20N.90N', '20S.20N', '30N.60N', '30S.00N', '60N.90N', '60S.30S', '60S.60N', '90S.00N', '90S.20S', '90S.60S', '90S.90N'}

def series(surface='land_ocean', frequency='ann', band='90S.90N', start=2000, end=2025):
    if surface not in {'land', 'ocean', 'land_ocean'} or frequency not in {'ann', 'mon'} or band not in BANDS:
        raise ValueError('invalid surface, frequency, or band')
    if isinstance(start, bool) or isinstance(end, bool) or (not 1850 <= int(start) <= int(end) <= 2100):
        raise ValueError('invalid date range')
    r = requests.get(BASE, timeout=30)
    r.raise_for_status()
    pattern = f'aravg\\.{frequency}\\.{surface}\\.{re.escape(band)}\\.v6\\.1\\.0\\.(\\d{{6}})\\.asc'
    matches = sorted(set(re.findall(pattern, r.text)))
    if not matches:
        raise ValueError('no matching official file')
    u = BASE + f'aravg.{frequency}.{surface}.{band}.v6.1.0.{matches[-1]}.asc'
    r = requests.get(u, timeout=30)
    r.raise_for_status()
    if len(r.content) > 1000000:
        raise ValueError('unexpected file size')
    out = []
    for line in r.text.splitlines():
        fields = line.split()
        expected = 10 if frequency == 'mon' else 6
        if len(fields) != expected:
            raise ValueError('unexpected field count')
        y = int(fields[0])
        offset = 2 if frequency == 'mon' else 1
        if not int(start) <= y <= int(end):
            continue
        nums = list(map(float, fields[offset:]))
        item = {'year': y, 'anomaly_K': nums[0], 'total_error_variance_K2': nums[1], 'high_frequency_error_variance_K2': nums[2], 'low_frequency_error_variance_K2': nums[3], 'bias_error_variance_K2': nums[4], 'source_fields': fields}
        if frequency == 'mon':
            item.update(month=int(fields[1]), diagnostics_raw=nums[5:])
        out.append(item)
    return {'provider': 'NOAA NCEI', 'dataset': 'NOAAGlobalTemp v6.1.0', 'source': u, 'baseline': '1991–2020', 'surface': surface, 'latitude_band': band, 'frequency': frequency, 'records': out, 'note': 'source_fields preserves original strings, including potential sentinel values; numeric columns remain unchanged. Consult official README before interpreting sentinel values.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--surface', choices=['land', 'ocean', 'land_ocean'], default='land_ocean')
    p.add_argument('--frequency', choices=['ann', 'mon'], default='ann')
    p.add_argument('--band', choices=sorted(BANDS), default='90S.90N')
    p.add_argument('--start', type=int, default=2000)
    p.add_argument('--end', type=int, default=2025)
    a = p.parse_args()
    print(json.dumps(series(a.surface, a.frequency, a.band, a.start, a.end), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
