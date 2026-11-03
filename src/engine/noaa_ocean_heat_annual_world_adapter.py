"""NOAA NCEI yearly World Ocean heat content anomaly, basin time series."""
import release_runtime
import requests
BASE = 'https://www.ncei.noaa.gov/data/oceans/woa/DATA_ANALYSIS/3M_HEAT_CONTENT/DATA/basin/yearly/'

def annual(depth=2000, start_year=2005, end_year=2025):
    if isinstance(depth, bool) or depth not in (700, 2000):
        raise ValueError('depth must be 700 or 2000 meters')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start_year, end_year))) or not 1955 <= start_year <= end_year <= 2100:
        raise ValueError('years must be integers from 1955 to 2100, in order')
    url = f'{BASE}h22-w0-{depth}m.dat'
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    if len(response.content) > 1000000:
        raise ValueError('Unexpected source file size')
    lines = response.text.strip().splitlines()
    if not lines or lines[0].split() != ['YEAR', 'WO', 'WOse', 'NH', 'NHse', 'SH', 'SHse']:
        raise ValueError('Unexpected NOAA source columns')
    rows = []
    for line in lines[1:]:
        cols = line.split()
        if len(cols) != 7:
            raise ValueError('Unexpected NOAA source row')
        vals = list(map(float, cols))
        year = int(vals[0])
        if start_year <= year <= end_year:
            rows.append({'year': year, 'decimal_year': vals[0], 'world': vals[1], 'world_standard_error': vals[2], 'north': vals[3], 'north_standard_error': vals[4], 'south': vals[5], 'south_standard_error': vals[6], 'source_fields': cols})
    return {'source_url': url, 'documentation': 'https://www.ncei.noaa.gov/access/global-ocean-heat-content/basin_heat_data.html', 'depth_meters': [0, depth], 'unit': '10^22 joules', 'scope': 'Annual World Ocean heat content anomaly, not absolute total heat; NOAA basin source with standard errors.', 'rows': rows}
