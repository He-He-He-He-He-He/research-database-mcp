"""United Nations WUP2025 F02 population shares, international definition."""
import release_runtime
from pathlib import Path
import openpyxl
FILE = Path(__file__).parent / '数据' / 'UN_WUP2025' / 'F02.xlsx'
SHEETS = {'rural': 'Rural', 'towns': 'Towns', 'cities': 'Cities', 'cities_towns': 'Cities and Towns'}

def share(location, year, category='cities_towns'):
    if category not in SHEETS:
        raise ValueError('invalid category')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1950 <= year <= 2050):
        raise ValueError('invalid year')
    if not isinstance(location, str) or not location.strip():
        raise ValueError('location required')
    w = openpyxl.load_workbook(FILE, read_only=True, data_only=True)
    try:
        sheet = w[SHEETS[category]]
        rows = sheet.iter_rows(values_only=True)
        headers = next(rows)
        if str(year) not in headers or 'ISO3_Code' not in headers:
            raise ValueError('unexpected workbook schema')
        y = headers.index(str(year))
        q = location.strip().casefold()
        found = []
        for row in rows:
            if q in (str(row[1]).casefold(), str(row[4] or '').casefold(), str(row[3])):
                found.append({'location': row[1], 'loc_id': row[3], 'iso3': row[4], 'location_type': row[8], 'notes': row[2], 'year': year, 'category': SHEETS[category], 'percent': row[y]})
        return {'source': 'UN WUP2025 F02', 'definition': 'international degree of urbanization', 'items': found, 'unit': 'percent', 'note': 'Estimates and projections; see UN methodology and notes.'}
    finally:
        w.close()
