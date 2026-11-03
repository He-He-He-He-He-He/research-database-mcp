"""Tuvalu Central Statistics Division GDP 2025 workbook."""
import release_runtime
import datetime, io
import requests
from openpyxl import load_workbook
URL = 'https://stats.gov.tv/download/70/national-accounts/2257/gdp-tables-2025'
PAGE = 'https://stats.gov.tv/category/economics/national-accounts/'

def table(sheet=None):
    if sheet is not None and sheet not in ('TOC', 'T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8'):
        raise ValueError('Invalid worksheet')
    with requests.get(URL, timeout=30, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for chunk in r.iter_content(65536):
            raw.extend(chunk)
            if len(raw) > 2000000:
                raise ValueError('Workbook too large')
        last_modified = r.headers.get('Last-Modified')
    w = load_workbook(io.BytesIO(raw), data_only=True)
    fw = load_workbook(io.BytesIO(raw), data_only=False)
    notes = ['Workbook contains 2016-base and 2023-base national accounts; do not splice different vintages or assume same values for nominal series.', 'Levels are in millions of Australian dollars; growth-rate tables are percent. Constant price bases are 2016 or 2023 as indicated on each sheet.', 'TOC names T7 as Table 7 and T8 as Table 8, while corresponding sheet headings read Table 6 and Table 7. Preserve this discrepancy.', 'Values, formulas, cached errors, formats, source row hierarchy and missing cells are not silently transformed; current file does not establish historical availability.']
    common = {'source': URL, 'source_page': PAGE, 'last_modified_header': last_modified, 'notes': notes}
    if sheet is None:
        return dict(common, sheets=w.sheetnames)
    s = w[sheet]
    f = fw[sheet]
    cells = []
    for row in s.iter_rows():
        for c in row:
            fc = f[c.coordinate]
            if c.value is None and fc.data_type != 'f':
                continue
            val = c.value.isoformat() if isinstance(c.value, (datetime.date, datetime.datetime)) else c.value
            cells.append({'cell': c.coordinate, 'value': val, 'value_type': c.data_type, 'formula': fc.value if fc.data_type == 'f' else None, 'number_format': c.number_format})
    return dict(common, sheet=sheet, merged_ranges=[str(x) for x in s.merged_cells.ranges], cells=cells)
