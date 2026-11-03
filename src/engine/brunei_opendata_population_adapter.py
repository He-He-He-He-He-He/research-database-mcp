"""Brunei government open-data catalog and a fixed population workbook."""
import release_runtime
import io
import requests
from openpyxl import load_workbook
CAT = 'https://www.data.gov.bn/wp-json/wp/v2/posts'
FILE = 'https://www.data.gov.bn/wp-content/uploads/2025/12/1-Mid-Year-Population-Estimate-2001-2013.xlsx'

def search(query='', page=1, limit=10):
    if not isinstance(query, str) or len(query) > 200 or type(page) is not int or (not 1 <= page <= 1000) or (type(limit) is not int) or (not 1 <= limit <= 50):
        raise ValueError('Invalid search or pagination')
    params = {'categories': 20, 'search': query, 'per_page': limit, 'page': page, '_fields': 'id,date,date_gmt,modified,modified_gmt,link,title,categories'}
    r = requests.get(CAT, params=params, timeout=30)
    r.raise_for_status()
    return {'source': CAT, 'params': params, 'total': int(r.headers['X-WP-Total']), 'pages': int(r.headers['X-WP-TotalPages']), 'records': r.json(), 'notes': ['Government open-data dataset posts; actual data owner and license vary by entry.', 'Post dates are publication or modification timestamps, not necessarily statistical reference dates.']}

def population():
    with requests.get(FILE, timeout=30, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for c in r.iter_content(65536):
            raw.extend(c)
            if len(raw) > 2000000:
                raise ValueError('Workbook too large')
        last_modified = r.headers.get('Last-Modified')
    w = load_workbook(io.BytesIO(raw), data_only=True)
    s = w['1']
    rows = []
    for row in s.iter_rows(min_col=1, max_col=8):
        cells = [{'coordinate': c.coordinate, 'value': c.value, 'number_format': c.number_format} for c in row if c.value is not None]
        if cells:
            rows.append(cells)
    merged = [str(x) for x in s.merged_cells.ranges]
    return {'source': FILE, 'source_page': 'https://www.data.gov.bn/mid-year-population-estimate-2/', 'last_modified_header': last_modified, 'sheet': s.title, 'included_columns': 'A:H', 'merged_ranges': merged, 'rows': rows, 'notes': ['Mid-year population estimates, 2001-2013; estimates not a complete census.', 'Original bilingual header, numeric values, formats and merged ranges retained, including total and sex-specific population and density, plus males per 1000 females.', 'Workbook timestamp and webpage publication/update date do not establish when each statistic first became available; this is the current downloadable file.', 'Only columns A:H are returned; other columns are not asserted empty.']}
