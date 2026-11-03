"""NOAA GML global marine surface SF6 monthly atmospheric mole fraction."""
import release_runtime
import re
import requests
URL = 'https://gml.noaa.gov/webdata/ccgg/trends/sf6/sf6_mm_gl.txt'

def monthly(start_year=2020, end_year=2026):
    if isinstance(start_year, bool) or isinstance(end_year, bool) or (not isinstance(start_year, int)) or (not isinstance(end_year, int)) or (not 1997 <= start_year <= end_year <= 2100):
        raise ValueError('Require integer years 1997 <= start_year <= end_year <= 2100')
    response = requests.get(URL, timeout=30)
    response.raise_for_status()
    if len(response.content) > 2000000:
        raise ValueError('Unexpected NOAA file size')
    raw = response.content.decode('utf-8')
    if 'average_unc' not in raw or 'trend_unc' not in raw:
        raise ValueError('Unexpected NOAA data format')
    created = re.search('^# File Creation:\\s*(.+)$', raw, re.M)
    rows = []
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        cols = line.split()
        if len(cols) != 7:
            raise ValueError('Unexpected NOAA data row')
        year, month = (int(cols[0]), int(cols[1]))
        if start_year <= year <= end_year:
            v = [float(x) for x in cols[2:]]
            rows.append({'year': year, 'month': month, 'decimal_year': v[0], 'average_ppt': v[1], 'average_uncertainty_ppt': None if v[2] < 0 else v[2], 'deseasonalized_trend_ppt': v[3], 'trend_uncertainty_ppt': None if v[4] < 0 else v[4], 'raw_values': dict(zip(('decimal_year', 'average', 'average_unc', 'trend', 'trend_unc'), cols[2:]))})
    return {'source_url': URL, 'documentation': 'https://gml.noaa.gov/ccgg/trends_sf6/', 'unit': 'pmol/mol dry air (ppt)', 'file_creation': created.group(1) if created else None, 'scope': 'Globally averaged marine surface atmospheric SF6 concentration; not emissions. Recent data are preliminary.', 'rows': rows}
