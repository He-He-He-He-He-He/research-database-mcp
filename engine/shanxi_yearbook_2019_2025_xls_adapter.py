"""Official Shanxi 2019–2025 yearbook XLS tables."""
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
ROOT = 'https://tjj.shanxi.gov.cn/tjsj/tjnj/'
YEARS = tuple(range(2019, 2026))

def _base(year):
    if isinstance(year, bool) or not isinstance(year, int) or year not in YEARS:
        raise ValueError('available editions: 2019–2025')
    return ROOT + f'nj{year}/zk/'

def catalog(year, keyword=''):
    base = _base(year)
    r = requests.get(base + 'lefte.htm', timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    out = []
    for a in s.select('a[href]'):
        path = a['href'].strip()
        title = ' '.join(a.get_text(' ', strip=True).split())
        if re.fullmatch('html/[A-Za-z0-9_-]+\\.xls', path, re.I) and title and (keyword in title):
            out.append({'id': path[5:-4], 'title': title, 'url': urljoin(base, path)})
    if not out and (not keyword):
        raise ValueError('catalog missing or changed')
    return {'source': f'山西省统计局《山西统计年鉴{year}》', 'edition': year, 'catalog_url': base + 'lefte.htm', 'items': out}

def table(year, table_id):
    if not isinstance(table_id, str) or not re.fullmatch('[A-Za-z0-9_-]+', table_id):
        raise ValueError('invalid table ID')
    m = [x for x in catalog(year)['items'] if x['id'] == table_id]
    if len(m) != 1:
        raise ValueError('table ID missing or ambiguous')
    r = requests.get(m[0]['url'], timeout=30)
    r.raise_for_status()
    if not r.content.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
        raise ValueError('response is not XLS')
    book = xlrd.open_workbook(file_contents=r.content, formatting_info=True)
    return {'source': f'山西省统计局《山西统计年鉴{year}》', 'edition': year, 'id': table_id, 'title': m[0]['title'], 'source_url': m[0]['url'], 'sheets': [{'name': s.name, 'rows': [s.row_values(i) for i in range(s.nrows)], 'merged_cells': [list(x) for x in s.merged_cells]} for s in book.sheets()], 'merged_cells_convention': '[row_start,row_end_exclusive,col_start,col_end_exclusive]'}
