"""FSM Statistics official GDP tables through FY2023."""
import release_runtime
import io, datetime
import requests
from openpyxl import load_workbook
URL = 'https://stats.gov.fm/download/12/national-accounts/2235/2023-fsm-gdp-tables.xlsx'
PAGE = 'https://stats.gov.fm/topics/economic-statistics/national-accounts-gdp/'

def table(sheet=None):
    if sheet is not None and sheet not in ('PerCapita', 'GDP'):
        raise ValueError('Unknown sheet')
    with requests.get(URL, timeout=30, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for part in r.iter_content(65536):
            raw.extend(part)
            if len(raw) > 2000000:
                raise ValueError('Workbook too large')
        last_modified = r.headers.get('Last-Modified')
    w = load_workbook(io.BytesIO(raw), data_only=True)
    fw = load_workbook(io.BytesIO(raw), data_only=False)
    common = {'source': URL, 'source_page': PAGE, 'last_modified_header': last_modified, 'notes': ['Fiscal years differ from calendar years. Constant-price GDP uses FY2004 prices; level units are millions of US dollars, per capita values are US dollars.', 'Source footnote states FY2013–FY2023 estimates are interim pending business gross-revenue administrative data.', 'Original n.a., zero, decimals, formulas, cached values, merged headings, formatting and notes remain distinct; population denominators can be estimated fractions.', 'Current downloadable workbook may have been revised; historical values are not proof of availability at prior cutoffs.']}
    if sheet is None:
        return dict(common, sheets=w.sheetnames)
    s = w[sheet]
    fs = fw[sheet]
    cells = []
    for row in s.iter_rows():
        for c in row:
            fc = fs[c.coordinate]
            if c.value is None and fc.data_type != 'f':
                continue
            v = c.value.isoformat() if isinstance(c.value, (datetime.date, datetime.datetime)) else c.value
            formula = {'type': type(fc.value).__name__, 'attributes': vars(fc.value)} if fc.data_type == 'f' and (not isinstance(fc.value, str)) else fc.value if fc.data_type == 'f' else None
            cells.append({'cell': c.coordinate, 'value': v, 'value_type': c.data_type, 'formula': formula, 'number_format': c.number_format})
    return dict(common, sheet=sheet, merged_ranges=[str(x) for x in s.merged_cells.ranges], cells=cells)
