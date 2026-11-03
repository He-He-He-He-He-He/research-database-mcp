"""UN WUP2025 F01 midyear population by international urbanization degree."""
import release_runtime
from pathlib import Path
import openpyxl
FILE = Path(__file__).parent / '数据' / 'UN_WUP2025' / 'F01.xlsx'
SHEETS = {'rural': 'Rural', 'towns': 'Towns', 'cities': 'Cities', 'cities_towns': 'Cities and Towns', 'total': 'Total'}

def population(location, year, category='total'):
    if category not in SHEETS:
        raise ValueError('invalid category')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1950 <= year <= 2050):
        raise ValueError('invalid year')
    if not isinstance(location, str) or not location.strip():
        raise ValueError('location required')
    w = openpyxl.load_workbook(FILE, read_only=True, data_only=True)
    try:
        rows = w[SHEETS[category]].iter_rows(values_only=True)
        header = next(rows)
        if str(year) not in header or 'ISO3_Code' not in header:
            raise ValueError('unexpected workbook schema')
        col = header.index(str(year))
        q = location.strip().casefold()
        items = []
        for row in rows:
            if q in (str(row[1]).casefold(), str(row[4] or '').casefold(), str(row[3])):
                items.append({'location': row[1], 'loc_id': row[3], 'iso3': row[4], 'location_type': row[8], 'notes': row[2], 'year': year, 'category': SHEETS[category], 'population_thousands': row[col]})
        return {'source': 'UN WUP2025 F01', 'definition': 'international degree of urbanization', 'unit': 'thousand persons', 'items': items, 'note': 'Estimates and projections using the international degree of urbanization; cities, towns and rural classifications may differ from national definitions. Do not treat this directly as a national official urbanization rate. Consult official methodology and location notes.'}
    finally:
        w.close()
