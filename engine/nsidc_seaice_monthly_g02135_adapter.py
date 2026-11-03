"""NSIDC/NOAA Sea Ice Index v4: a hemisphere and month across years."""
import release_runtime
import csv, io
import requests
BASE = 'https://noaadata.apps.nsidc.org/NOAA/G02135'

def monthly(hemisphere, month, start_year=1979, end_year=2026):
    if hemisphere not in ('north', 'south'):
        raise ValueError('hemisphere must be north or south')
    if isinstance(month, bool) or not isinstance(month, int) or (not 1 <= month <= 12):
        raise ValueError('month must be 1 through 12')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start_year, end_year))) or not 1978 <= start_year <= end_year <= 2100:
        raise ValueError('years must be integers 1978 through 2100, in order')
    region = 'N' if hemisphere == 'north' else 'S'
    url = f'{BASE}/{hemisphere}/monthly/data/{region}_{month:02d}_extent_v4.0.csv'
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    if len(response.content) > 1000000:
        raise ValueError('Unexpected source size')
    reader = csv.DictReader(io.StringIO(response.content.decode('utf-8-sig')), skipinitialspace=True)
    if not reader.fieldnames or {v.strip() for v in reader.fieldnames} != {'year', 'mo', 'source_dataset', 'region', 'extent', 'area'}:
        raise ValueError('Unexpected source columns')
    rows = []
    for raw in reader:
        d = {k.strip(): v.strip() for k, v in raw.items()}
        year, mo = (int(d['year']), int(d['mo']))
        if mo != month or d['region'] != region:
            raise ValueError('Unexpected month or hemisphere in source')
        if start_year <= year <= end_year:
            rows.append({'year': year, 'month': mo, 'source_dataset': d['source_dataset'], 'extent_million_km2': float(d['extent']), 'area_million_km2': float(d['area']), 'raw_row': d})
    return {'source_url': url, 'documentation': 'https://nsidc.org/data/seaice_index/data-and-image-archive', 'hemisphere': hemisphere, 'month': month, 'unit': 'million square kilometers', 'scope': 'Monthly sea ice extent and area; extent and area use different definitions. Input dataset can change across time.', 'rows': rows}
