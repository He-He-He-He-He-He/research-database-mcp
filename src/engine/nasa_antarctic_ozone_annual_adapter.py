"""NASA Ozone Watch Antarctic annual records and seasonal averages."""
import release_runtime
import requests
from bs4 import BeautifulSoup
URL = 'https://ozonewatch.gsfc.nasa.gov/statistics/annual_data.html'

def annual(start_year=2000, end_year=2025):
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start_year, end_year))) or not 1979 <= start_year <= end_year <= 2100:
        raise ValueError('Year range must be integers 1979–2100 in order')
    r = requests.get(URL, timeout=30)
    r.raise_for_status()
    if len(r.content) > 2000000:
        raise ValueError('Unexpected source size')
    soup = BeautifulSoup(r.content, 'html.parser')
    tables = soup.select('table')
    if len(tables) != 2:
        raise ValueError('Unexpected NASA annual table structure')
    results = []
    for i, table in enumerate(tables):
        header = table.get_text(' ', strip=True)[:300]
        if 'Ozone Hole Area' not in header or 'Minimum Ozone' not in header:
            raise ValueError('Unexpected NASA table headings')
        rows = []
        for tr in table.select('tr'):
            cols = [v.get_text(' ', strip=True) for v in tr.select('th,td')]
            if not cols or not cols[0].isdigit() or len(cols[0]) != 4:
                continue
            if len(cols) != (5 if i == 0 else 3):
                raise ValueError('Unexpected NASA table row')
            year = int(cols[0])
            if not start_year <= year <= end_year:
                continue
            if i == 0:
                rows.append({'year': year, 'maximum_area_date': cols[1], 'maximum_area_million_km2': float(cols[2]), 'minimum_ozone_date': cols[3], 'minimum_ozone_du': float(cols[4]), 'source_cells': cols})
            else:
                rows.append({'year': year, 'mean_area_sep7_oct13_million_km2': float(cols[1]), 'mean_minimum_ozone_sep21_oct16_du': float(cols[2]), 'source_cells': cols})
        results.append(rows)
    return {'source_url': URL, 'source': 'NASA Ozone Watch', 'annual_daily_extrema': results[0], 'seasonal_means': results[1], 'note': 'Daily maximum area is different from Sep 7–Oct 13 mean. No 1995 data in NASA source; missing year is not zero.'}
