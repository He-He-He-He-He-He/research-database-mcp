"""CARICOM government operations workbooks for six countries/territories."""
import release_runtime
import datetime, io
import requests
from openpyxl import load_workbook
PAGE = 'https://statistics.caricom.org/?data_categories=government-finance-statistics&paged=2'
FILES = {'LC': '2012_2024', 'KN': '2012_2024', 'VC': '2012_2024', 'SR-old': '2012_2018', 'SR': '2019_2024', 'TT': '2012_2024', 'TC': '2012_2020'}

def table(code):
    if code not in FILES:
        raise ValueError('Unknown code; choose LC, KN, VC, SR-old, SR, TT or TC')
    country = code.split('-')[0]
    url = 'https://statistics.caricom.org/wp-content/uploads/2025/09/Governmentoperations_' + country + '_' + FILES[code] + '.xlsx'
    with requests.get(url, timeout=30, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for c in r.iter_content(65536):
            raw.extend(c)
            if len(raw) > 2000000:
                raise ValueError('Workbook too large')
        modified = r.headers.get('Last-Modified')
    w = load_workbook(io.BytesIO(raw), data_only=True)
    f = load_workbook(io.BytesIO(raw), data_only=False)
    s = w.active
    fs = f[s.title]
    cells = []
    for row in s.iter_rows():
        for c in row:
            fc = fs[c.coordinate]
            if c.value is None and fc.data_type != 'f':
                continue
            val = c.value.isoformat() if isinstance(c.value, (datetime.date, datetime.datetime)) else c.value
            formula = {'type': type(fc.value).__name__, 'attributes': vars(fc.value)} if fc.data_type == 'f' and (not isinstance(fc.value, str)) else fc.value if fc.data_type == 'f' else None
            cells.append({'cell': c.coordinate, 'value': val, 'value_type': c.data_type, 'formula': formula, 'number_format': c.number_format, 'indent': c.alignment.indent})
    return {'source': url, 'source_page': PAGE, 'country_code': code, 'sheet': s.title, 'last_modified_header': modified, 'merged_ranges': [str(x) for x in s.merged_cells.ranges], 'cells': cells, 'notes': ['CARICOM regional compilation; source institutions vary by workbook, consult the embedded source lines.', 'Each workbook contains separate currency blocks, including EC dollars and US dollars; some also contain national currency. Labels are preserved; do not sum blocks.', 'Central government operations are not the whole economy. Parent and child fiscal rows, grants and balancing concepts must be kept distinct.', 'Suriname has separate periods SR-old (2012–2018) and SR (2019–2024), which may differ in basis; inspect notes before joining.', 'Published/downloaded version may postdate earlier analysis cutoffs; historical values may be revised.']}
