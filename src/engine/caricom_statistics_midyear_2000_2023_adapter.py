"""CARICOM regional statistics mid-year population workbook, 2000-2023."""
import release_runtime
import io
import requests
from openpyxl import load_workbook
URL = 'https://statistics.caricom.org/wp-content/uploads/2025/09/Mid-Year-Estimates-2000-2023.xlsx'
PAGE = 'https://statistics.caricom.org/?data_categories=population'

def population():
    with requests.get(URL, timeout=30, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for c in r.iter_content(65536):
            raw.extend(c)
            if len(raw) > 2000000:
                raise ValueError('Workbook exceeds size limit')
        last_modified = r.headers.get('Last-Modified')
    cached = load_workbook(io.BytesIO(raw), data_only=True)
    formula = load_workbook(io.BytesIO(raw), data_only=False)
    s = cached['Sheet1']
    f = formula['Sheet1']
    rows = []
    for row in s.iter_rows():
        items = []
        for c in row:
            if c.value is None and f[c.coordinate].data_type != 'f':
                continue
            color = c.font.color
            color_desc = None if color is None else {'type': color.type, 'value': getattr(color, color.type, None), 'tint': color.tint}
            items.append({'cell': c.coordinate, 'value': c.value, 'formula': f[c.coordinate].value if f[c.coordinate].data_type == 'f' else None, 'number_format': c.number_format, 'font_color': color_desc})
        if items:
            rows.append(items)
    return {'source': URL, 'source_page': PAGE, 'http_last_modified': last_modified, 'sheet': s.title, 'merged_ranges': [str(x) for x in s.merged_cells.ranges], 'rows': rows, 'notes': ['CARICOM regional compilation from official national sources and its Regional Statistics Programme; country values and regional aggregations are estimates with distinct geographic coverage.', 'Source states estimates are as of July 1, but Cayman Islands uses end-of-year estimates. Red font indicates values repeated from the previous year; font colours and original notes are preserved.', 'Displayed population is formatted as whole persons while underlying spreadsheet cells can contain decimals; numeric values and number formats are preserved without rounding.', 'An upload or file timestamp is not evidence that data were available at an earlier research cutoff.']}
