"""Official Inner Mongolia yearbook and 2020 census XLS data."""
import release_runtime
import re, sys
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
try:
    import xlrd
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
    import xlrd
ROOT = 'https://tj.nmg.gov.cn/files_pub/content/PAGEPACK/'
BOOKS = {'2020': ('内蒙古统计年鉴2020', 'b85658190a3644f8b192e45f5221f2fa/zk/'), '2021': ('内蒙古统计年鉴2021', '83e5521da4e94d50ab45483b58e5fa7e/zk/'), '2023': ('内蒙古统计年鉴2023', '7f2e427b72bc45ec84f1773389947068/zk/'), 'census2020': ('内蒙古自治区人口普查年鉴2020', 'zk2020/')}

def catalog(book, keyword=''):
    if book not in BOOKS:
        raise ValueError('unknown book; see BOOKS')
    name, path = BOOKS[book]
    base = ROOT + path
    r = requests.get(base + 'lefte.htm', timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    out = []
    for a in s.select('a[href]'):
        p = a['href'].strip()
        title = ' '.join(a.get_text(' ', strip=True).split())
        if re.fullmatch('html/[A-Za-z0-9_-]+\\.xls', p, re.I) and title and (keyword in title):
            out.append({'id': p[5:-4], 'title': title, 'url': urljoin(base, p)})
    if not out and (not keyword):
        raise ValueError('catalog missing or changed')
    return {'source': name, 'book': book, 'catalog_url': base + 'lefte.htm', 'items': out}

def table(book, table_id):
    if not isinstance(table_id, str) or not re.fullmatch('[A-Za-z0-9_-]+', table_id):
        raise ValueError('invalid table ID')
    c = catalog(book)
    m = [x for x in c['items'] if x['id'] == table_id]
    if len(m) != 1:
        raise ValueError('table ID missing or ambiguous')
    r = requests.get(m[0]['url'], timeout=30)
    r.raise_for_status()
    if not r.content.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
        raise ValueError('response is not XLS')
    w = xlrd.open_workbook(file_contents=r.content, formatting_info=True)
    return {'source': c['source'], 'book': book, 'id': table_id, 'title': m[0]['title'], 'source_url': m[0]['url'], 'sheets': [{'name': s.name, 'rows': [s.row_values(i) for i in range(s.nrows)], 'merged_cells': [list(x) for x in s.merged_cells]} for s in w.sheets()], 'merged_cells_convention': '[row_start,row_end_exclusive,col_start,col_end_exclusive]'}
