"""Bank of Botswana BEFS official monthly multi-topic workbook reader."""
import release_runtime
import io, zipfile, datetime
from urllib.parse import urljoin, urlparse
import requests, openpyxl
from bs4 import BeautifulSoup
PAGE = 'https://www.bankofbotswana.bw/botswana-economic-and-financial-statistics'
HOST = 'www.bankofbotswana.bw'
MAX = 12000000

def _get(url):
    u = urlparse(url)
    if u.scheme != 'https' or u.hostname != HOST or u.port or u.username or u.password:
        raise ValueError('invalid official URL')
    with requests.get(url, timeout=45, allow_redirects=False, stream=True) as r:
        r.raise_for_status()
        if r.status_code != 200:
            raise RuntimeError('unexpected upstream status')
        size = 0
        parts = []
        for part in r.iter_content(65536):
            size += len(part)
            if size > MAX:
                raise RuntimeError('response exceeds 12 MB')
            parts.append(part)
    return b''.join(parts)

def catalogue(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 150:
        raise ValueError('invalid keyword')
    soup = BeautifulSoup(_get(PAGE), 'html.parser')
    out = []
    for row in soup.find_all('tr'):
        a = row.find('a', href=True)
        cells = row.find_all('td', recursive=False)
        if not a or len(cells) < 2:
            continue
        url = urljoin(PAGE, a['href'].strip())
        u = urlparse(url)
        if u.scheme != 'https' or u.hostname != HOST or (not u.path.startswith('/sites/default/files/publications/')) or (not u.path.lower().endswith('.xlsx')):
            continue
        title = ' '.join(cells[1].get_text(' ', strip=True).split())
        release = ' '.join(cells[0].get_text(' ', strip=True).split())
        if keyword.casefold() in title.casefold():
            out.append({'title': title, 'publication_month': release, 'url': url})
    if not out and (not keyword):
        raise RuntimeError('official catalogue layout changed')
    return {'source': PAGE, 'matched': len(out), 'editions': out, 'note': 'Publication month and workbook title period differ; table coverage and source vary.'}

def _workbook(title):
    if not isinstance(title, str) or len(title) > 200:
        raise ValueError('invalid edition')
    entries = [x for x in catalogue()['editions'] if x['title'] == title]
    if len(entries) != 1:
        raise ValueError('edition is not uniquely present in official catalogue')
    data = _get(entries[0]['url'])
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if sum((x.file_size for x in z.infolist())) > 100000000:
            raise RuntimeError('workbook expanded size exceeds 100 MB')
    return (entries[0], openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True))

def sheets(title):
    entry, w = _workbook(title)
    try:
        return {'edition': entry, 'sheets': w.sheetnames, 'note': 'Sheet names only; values and units require table inspection.'}
    finally:
        w.close()

def table(title, sheet, start=1, limit=50, max_cols=40):
    if not isinstance(sheet, str) or len(sheet) > 100:
        raise ValueError('invalid sheet')
    for val in (start, limit, max_cols):
        if isinstance(val, bool) or not isinstance(val, int):
            raise ValueError('pagination must be integers')
    if start < 1 or not 1 <= limit <= 200 or (not 1 <= max_cols <= 100):
        raise ValueError('invalid bounds')
    entry, w = _workbook(title)
    try:
        if sheet not in w.sheetnames:
            raise ValueError('unknown sheet')
        sh = w[sheet]
        out = []
        for cells in sh.iter_rows(min_row=start, max_row=start + limit - 1, max_col=max_cols, values_only=True):
            row = [v.isoformat() if isinstance(v, (datetime.datetime, datetime.date, datetime.time)) else v for v in cells]
            out.append(row)
        return {'edition': entry, 'sheet': sheet, 'sheet_rows': sh.max_row, 'sheet_columns': sh.max_column, 'start_row': start, 'max_cols': max_cols, 'rows': out, 'note': 'Original cached cell values; headers/footnotes may lie outside this slice. Nonempty cells beyond max_cols are omitted; formulas return cached values, which may be stale or absent.'}
    finally:
        w.close()
