"""CARICOM merchandise trade indicators official workbook."""
import release_runtime
import datetime, io
import requests
from openpyxl import load_workbook
URL = 'https://statistics.caricom.org/wp-content/uploads/2026/08/CARICOM-TRADE-SUMMARY-1973-2024.xlsx'
PAGE = 'https://statistics.caricom.org/?data_categories=caricom-total-trade'

def trade():
    with requests.get(URL, timeout=30, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for c in r.iter_content(65536):
            raw.extend(c)
            if len(raw) > 2000000:
                raise ValueError('Workbook too large')
        last_modified = r.headers.get('Last-Modified')
    a = load_workbook(io.BytesIO(raw), data_only=True)
    b = load_workbook(io.BytesIO(raw), data_only=False)
    s = a['Total Exports']
    f = b['Total Exports']
    rows = []
    for row in s.iter_rows():
        cells = []
        for c in row:
            formula = f[c.coordinate]
            if c.value is None and formula.data_type != 'f':
                continue
            value = c.value.isoformat() if isinstance(c.value, (datetime.date, datetime.datetime)) else c.value
            color = c.font.color
            cells.append({'cell': c.coordinate, 'value': value, 'value_type': 'datetime' if isinstance(c.value, (datetime.date, datetime.datetime)) else c.data_type, 'formula': formula.value if formula.data_type == 'f' else None, 'number_format': c.number_format, 'font_color': None if color is None else {'type': color.type, 'value': getattr(color, color.type, None), 'tint': color.tint}})
        if cells:
            rows.append(cells)
    return {'source': URL, 'source_page': PAGE, 'last_modified_header': last_modified, 'sheet': s.title, 'merged_ranges': [str(x) for x in s.merged_cells.ranges], 'rows': rows, 'notes': ['CARICOM source page and file name say 1973–2024, but workbook heading and rows cover 2000–2024; do not infer data for 1973–1999.', 'Workbook says updated July 2026 and current US dollars: monetary columns use million USD, percentage columns have different units; preserve individual headers.', 'Merchandise trade totals and intra-regional trade are distinct; raw formulas and cached values are not independently recomputed.', 'Current file and revised historical values are not evidence of what was available before 2025-06.']}
