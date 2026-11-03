"""Tonga Statistics Department 2021 census population and household income tables."""
import release_runtime
import io, datetime
import requests
from openpyxl import load_workbook
PAGE = 'https://tongastats.gov.to/census-2/population-census-3/census-tables/'
URLS = {'population': 'https://tongastats.gov.to/download/266/general-tables/8089/1-population-trends.xlsx', 'income': 'https://tongastats.gov.to/download/275/household-tables/7678/3-household-income.xlsx'}

def table(workbook='population', sheet=None):
    if workbook not in URLS or (sheet is not None and (not isinstance(sheet, str) or len(sheet) > 31)):
        raise ValueError('Invalid workbook or sheet')
    with requests.get(URLS[workbook], timeout=30, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for b in r.iter_content(65536):
            raw.extend(b)
            if len(raw) > 3000000:
                raise ValueError('Workbook exceeds size limit')
        last_modified = r.headers.get('Last-Modified')
    vals = load_workbook(io.BytesIO(raw), data_only=True)
    forms = load_workbook(io.BytesIO(raw), data_only=False)
    if sheet is None:
        return {'source': URLS[workbook], 'source_page': PAGE, 'last_modified_header': last_modified, 'sheets': vals.sheetnames, 'notes': ['Select a sheet to retrieve the raw official census table.', 'Reference population and household base may vary across sheets.']}
    if sheet not in vals.sheetnames:
        raise ValueError('Unknown sheet')
    s = vals[sheet]
    f = forms[sheet]
    if s.max_row * s.max_column > 50000:
        raise ValueError('Sheet too large')
    rows = []
    for row in s.iter_rows():
        cells = []
        for c in row:
            fc = f[c.coordinate]
            if c.value is None and fc.data_type != 'f':
                continue
            v = c.value.isoformat() if isinstance(c.value, (datetime.date, datetime.datetime)) else c.value
            cells.append({'cell': c.coordinate, 'value': v, 'formula': fc.value if fc.data_type == 'f' else None, 'number_format': c.number_format})
        if cells:
            rows.append(cells)
    return {'source': URLS[workbook], 'source_page': PAGE, 'last_modified_header': last_modified, 'sheet': sheet, 'merged_ranges': [str(x) for x in s.merged_cells.ranges], 'rows': rows, 'notes': ['2021 census tables can include earlier census years; check column and row headers, hierarchy and source notes.', 'Total population, household population and household counts are distinct; household income source counts are not income amounts.', 'Underlying values, number formats, cached formulas and merged headers preserved; omitted blank cells are not zeros.', 'The current downloadable file may have been revised; a file date alone does not prove historical availability.']}
