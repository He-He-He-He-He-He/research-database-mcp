"""Kiribati National Statistics Office national accounts workbook."""
import release_runtime
import io, datetime
import requests
from openpyxl import load_workbook
URL = 'https://nso.gov.ki/download/52/gross-domestic-product/2180/gdp-master-table_2024'
PAGE = 'https://nso.gov.ki/documents/'

def table(sheet=None):
    if sheet is not None and (not isinstance(sheet, str) or len(sheet) > 31):
        raise ValueError('Invalid sheet')
    with requests.get(URL, timeout=30, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for part in r.iter_content(65536):
            raw.extend(part)
            if len(raw) > 4000000:
                raise ValueError('Workbook too large')
        last_modified = r.headers.get('Last-Modified')
    vals = load_workbook(io.BytesIO(raw), data_only=True)
    forms = load_workbook(io.BytesIO(raw), data_only=False)
    notes = ['Current-price national accounts are in thousands of Australian dollars, constant-price tables use 2019 prices, and deflators use 2019=100. Check each sheet title and units.', 'The file is listed as GDP master table 2024 while the cover states year ending December 2023; preserve the conflict and verify actual series years.', 'Some source cells contain #REF! errors; preserve these, never treat them as valid values or zeros. Formula cached results may be stale or missing.', 'Current workbook and historical series can be revised; workbook metadata is not evidence of historical public availability.']
    common = {'source': URL, 'source_page': PAGE, 'last_modified_header': last_modified, 'notes': notes}
    if sheet is None:
        return dict(common, sheets=vals.sheetnames)
    if sheet not in vals.sheetnames:
        raise ValueError('Unknown sheet')
    s = vals[sheet]
    f = forms[sheet]
    cells = []
    for (row, col), c in sorted(s._cells.items()):
        fc = f.cell(row, col)
        if c.value is None and fc.data_type != 'f':
            continue
        v = c.value.isoformat() if isinstance(c.value, (datetime.date, datetime.datetime)) else c.value
        cells.append({'cell': c.coordinate, 'value': v, 'value_type': c.data_type, 'formula': fc.value if fc.data_type == 'f' else None, 'number_format': c.number_format})
        if len(cells) > 30000:
            raise ValueError('Sheet exceeds non-empty cell limit')
    return dict(common, sheet=sheet, merged_ranges=[str(x) for x in s.merged_cells.ranges], cells=cells)
