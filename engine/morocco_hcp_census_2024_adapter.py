"""Morocco HCP 2024 census legal population original workbook."""
import release_runtime
import hashlib
import io
import warnings
import requests
import openpyxl
URL = 'https://www.hcp.ma/file/242341/'
PAGE = 'https://www.hcp.ma/downloads/RGPH-2024_t22752.html'
NOTES = ["Official HCP 2024 census legal population, using the source's territorial categories and boundaries; this is a census reference, not a current population estimate.", 'National, regional, urban, rural, provincial and communal rows overlap; do not sum all results. Search is literal against the original French/Arabic labels and geographic code.', 'Preserve original bilingual headings, raw geographic codes and footnote indicators. The source footnote identifies data obtained from local administration because of seasonal mobility.', 'The HCP catalogue lists the workbook on 22 November 2024, but the current downloadable file may have changed; inspect its hash and metadata when exact historical provenance is required.']

def search(keyword, limit=20, offset=0):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100 or (type(limit) is not int) or (not 1 <= limit <= 100) or (type(offset) is not int) or (offset < 0):
        raise ValueError('Invalid query')
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    if not r.content.startswith(b'PK'):
        raise ValueError('HCP source is not XLSX')
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='Print area cannot be set.*')
        w = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)
    if 'Population_légale' not in w.sheetnames:
        raise ValueError('Unexpected HCP workbook')
    s = w['Population_légale']
    head = [list(row) for row in s.iter_rows(min_row=1, max_row=7, max_col=7, values_only=True)]
    if head[5][0] != 'Collectivités territoriales' or head[6][3] != 'Population':
        raise ValueError('Unexpected HCP headings')
    rows = []
    footnotes = []
    term = keyword.casefold()
    for idx, row in enumerate(s.iter_rows(min_row=8, max_col=7, values_only=True), 8):
        if row[0] and row[3] is None:
            footnotes.append({'row': idx, 'text': row[0]})
            continue
        if row[0] is None or row[3] is None:
            continue
        if term in ' '.join((str(row[i] or '') for i in (0, 5, 6))).casefold():
            rows.append({'source_row': idx, 'cells': list(row[:7])})
    return {'source': URL, 'catalogue': PAGE, 'census_year': 2024, 'http_last_modified': r.headers.get('Last-Modified'), 'sha256': hashlib.sha256(r.content).hexdigest(), 'header_rows': head, 'footnotes': footnotes, 'total_matching': len(rows), 'offset': offset, 'notes': NOTES, 'records': rows[offset:offset + limit]}
