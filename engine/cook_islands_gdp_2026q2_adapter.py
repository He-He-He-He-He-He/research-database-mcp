"""Cook Islands Statistics Office GDP June quarter 2026 workbook."""
import release_runtime
import datetime, io
import requests
from openpyxl import load_workbook
URL = 'https://stats.gov.ck/download/532/2026/8182/gross-domestic-product-june-quarter-2026.xlsx'
PAGE = 'https://stats.gov.ck/national-accounts/'

def table(sheet=None):
    if sheet is not None and sheet not in ('Contents', 'Table 1', 'Table 2', 'Table 3', 'Table 4'):
        raise ValueError('Unknown sheet')
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
    common = {'source': URL, 'source_page': PAGE, 'last_modified_header': last_modified, 'notes': ['GDP tables cover current prices, constant 2016 prices and corresponding percentage changes by industry; preserve separate units and headers.', 'Dollar values are millions and must be interpreted in the source currency; quarter dates use Excel date cells and formatting, not daily GDP.', 'Quarterly values may be seasonal and revised; compare periods carefully and consult the source methodology.', 'This June 2026 release is not evidence of data available before its release, even for earlier quarters.']}
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
            v = c.value.isoformat() if isinstance(c.value, (datetime.date, datetime.datetime)) else c.value
            cells.append({'cell': c.coordinate, 'value': v, 'value_type': c.data_type, 'formula': fc.value if fc.data_type == 'f' else None, 'number_format': c.number_format})
    return dict(common, sheet=sheet, merged_ranges=[str(x) for x in s.merged_cells.ranges], cells=cells)
