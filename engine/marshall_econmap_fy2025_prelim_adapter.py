"""RMI FY25 preliminary economic statistics: EconMAP with EPPSO."""
import release_runtime
import io, datetime
import requests
from openpyxl import load_workbook
URL = 'https://pitiviti.org/storage/dm/2026/05/rmi-econstat-tabs-fy25-prelim-pub1-20260528053041884.xlsx'
PAGE = 'https://pubs.pitiviti.org/rmi-fy25-economic-statistics-preliminary'

def table(sheet=None):
    if sheet is not None and (not isinstance(sheet, str) or len(sheet) > 31):
        raise ValueError('Invalid sheet')
    with requests.get(URL, timeout=40, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for c in r.iter_content(65536):
            raw.extend(c)
            if len(raw) > 6000000:
                raise ValueError('Workbook too large')
        last_modified = r.headers.get('Last-Modified')
    w = load_workbook(io.BytesIO(raw), data_only=True)
    f = load_workbook(io.BytesIO(raw), data_only=False)
    notes = ['EconMAP publication prepared in collaboration with RMI Economic Policy, Planning and Statistics Office; FY2025 publication is preliminary and subject to revision.', 'Series use fiscal years or calendar years as labeled per table; do not equate them. Units and population estimates vary across sheets.', 'Underlying values, displayed formats, footnotes, formula cache and formulas are retained; verify assumptions and original worksheets.', 'Released in 2026 and cannot establish what was available at earlier cutoffs.']
    common = {'source': URL, 'source_page': PAGE, 'last_modified_header': last_modified, 'notes': notes}
    if sheet is None:
        return dict(common, sheets=w.sheetnames)
    if sheet not in w.sheetnames:
        raise ValueError('Unknown sheet')
    s = w[sheet]
    fs = f[sheet]
    if not hasattr(s, '_cells'):
        raise ValueError('Selected sheet is a chart, not a data worksheet')
    cells = []
    for pos, c in sorted(s._cells.items()):
        fc = fs.cell(*pos)
        if c.value is None and fc.data_type != 'f':
            continue
        value = c.value.isoformat() if isinstance(c.value, (datetime.date, datetime.datetime)) else c.value
        color = c.font.color
        cells.append({'cell': c.coordinate, 'value': value, 'value_type': c.data_type, 'formula': {'type': type(fc.value).__name__, 'attributes': vars(fc.value)} if fc.data_type == 'f' and (not isinstance(fc.value, str)) else fc.value if fc.data_type == 'f' else None, 'number_format': c.number_format, 'font_color': None if color is None else {'type': color.type, 'value': getattr(color, color.type, None), 'tint': color.tint}})
        if len(cells) > 30000:
            raise ValueError('Sheet exceeds non-empty cell limit')
    return dict(common, sheet=sheet, merged_ranges=[str(x) for x in s.merged_cells.ranges], cells=cells)
