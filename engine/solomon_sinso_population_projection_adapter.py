"""Solomon Islands National Statistics Office population projection workbook."""
import release_runtime
import io, datetime
import requests
from openpyxl import load_workbook
URL = 'https://statistics.gov.sb/download/21/population/686/national-population-projection'
PAGE = 'https://statistics.gov.sb/category/statistics/social-statistics/population/'

def projection(year):
    if type(year) is not int or not 2010 <= year <= 2025:
        raise ValueError('year must be 2010 to 2025')
    with requests.get(URL, timeout=30, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for b in r.iter_content(65536):
            raw.extend(b)
            if len(raw) > 2000000:
                raise ValueError('Workbook too large')
        last_modified = r.headers.get('Last-Modified')
    values = load_workbook(io.BytesIO(raw), data_only=True)
    formulas = load_workbook(io.BytesIO(raw), data_only=False)
    names = [n for n in values.sheetnames if n.strip() == str(year)]
    if len(names) != 1:
        raise ValueError('Year sheet missing or ambiguous')
    s = values[names[0]]
    f = formulas[names[0]]
    rows = []
    for row in s.iter_rows():
        cells = []
        for c in row:
            fc = f[c.coordinate]
            if c.value is None and fc.data_type != 'f':
                continue
            v = c.value.isoformat() if isinstance(c.value, (datetime.date, datetime.datetime)) else c.value
            color = c.font.color
            cells.append({'cell': c.coordinate, 'value': v, 'formula': fc.value if fc.data_type == 'f' else None, 'number_format': c.number_format, 'font_color': None if color is None else {'type': color.type, 'value': getattr(color, color.type, None), 'tint': color.tint}})
        if cells:
            rows.append(cells)
    return {'source': URL, 'source_page': PAGE, 'last_modified_header': last_modified, 'workbook_created_metadata': values.properties.created.isoformat() if values.properties.created else None, 'workbook_modified_metadata': values.properties.modified.isoformat() if values.properties.modified else None, 'sheet': s.title, 'merged_ranges': [str(x) for x in s.merged_cells.ranges], 'rows': rows, 'notes': ['National population projections, not census counts or necessarily current estimates. The projection model, baseline and publication vintage have not been verified; assess against the latest census and releases.', 'Each worksheet contains single-year and five-year age-group tables with male, female and total values. Each sheet has its own layout and original headers; no inferred column mapping.', 'Values may have fractional population estimates; number formats and formula cache are retained rather than silently rounded. Omitted cells are blank, not zero.', 'Workbook internal metadata dates do not prove public release time or projection baseline.']}
