"""CARICOM compilation of Grenada central government operations."""
import release_runtime
import datetime, io
import requests
from openpyxl import load_workbook
URL = 'https://statistics.caricom.org/wp-content/uploads/2025/09/Governmentoperations_GD_2012_2024.xlsx'
PAGE = 'https://statistics.caricom.org/data_categories/2-economic-statistics/page/12/'

def table():
    with requests.get(URL, timeout=30, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for c in r.iter_content(65536):
            raw.extend(c)
            if len(raw) > 2000000:
                raise ValueError('Workbook too large')
        modified = r.headers.get('Last-Modified')
    w = load_workbook(io.BytesIO(raw), data_only=True)
    f = load_workbook(io.BytesIO(raw), data_only=False)
    s = w['GDECCBFORMAT']
    fs = f['GDECCBFORMAT']
    cells = []
    for row in s.iter_rows():
        for c in row:
            fc = fs[c.coordinate]
            if c.value is None and fc.data_type != 'f':
                continue
            v = c.value.isoformat() if isinstance(c.value, (datetime.date, datetime.datetime)) else c.value
            formula = {'type': type(fc.value).__name__, 'attributes': vars(fc.value)} if fc.data_type == 'f' and (not isinstance(fc.value, str)) else fc.value if fc.data_type == 'f' else None
            cells.append({'cell': c.coordinate, 'value': v, 'value_type': c.data_type, 'formula': formula, 'number_format': c.number_format, 'indent': c.alignment.indent})
    return {'source': URL, 'source_page': PAGE, 'last_modified_header': modified, 'sheet': s.title, 'merged_ranges': [str(x) for x in s.merged_cells.ranges], 'cells': cells, 'notes': ['CARICOM publication; workbook cites Eastern Caribbean Central Bank as source. It reports central government operations, not the entire economy or general government.', 'The first block is millions of Eastern Caribbean dollars; the second is millions of US dollars. Do not sum or confuse both blocks.', 'Fiscal categories are hierarchical, including before/after grants; raw formulas, indentation, format and values are retained.', 'Source file HTTP modification date is September 2025; historical values do not establish availability or vintage before June 2025.']}
