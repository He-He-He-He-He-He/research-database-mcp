"""Official Shaanxi 2017 yearbook, catalog and same-stem XLS originals."""
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
BASE = 'https://tjj.shaanxi.gov.cn/upload/2018/7/zk/'

def catalog(keyword=''):
    r = requests.get(BASE + 'left.htm', timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    out = []
    for a in s.select('a[href]'):
        p = a['href'].strip()
        title = ' '.join(a.get_text(' ', strip=True).split())
        if re.fullmatch('html/[A-Za-z0-9_-]+\\.jpg', p, re.I) and re.match('^\\d+-\\d+', title) and (keyword in title):
            out.append({'id': p[5:-4], 'title': title, 'image_url': urljoin(BASE, p), 'xls_candidate_url': urljoin(BASE, p[:-4] + '.xls')})
    if not out and (not keyword):
        raise ValueError('catalog missing or changed')
    return {'source': '陕西省统计局《陕西统计年鉴2017》', 'edition': 2017, 'catalog_url': BASE + 'left.htm', 'items': out, 'note': 'XLS addresses are derived from image names and checked only when table is requested.'}

def table(table_id):
    if not isinstance(table_id, str) or not re.fullmatch('[A-Za-z0-9_-]+', table_id):
        raise ValueError('invalid table ID')
    m = [x for x in catalog()['items'] if x['id'] == table_id]
    if len(m) != 1:
        raise ValueError('table ID missing or ambiguous')
    r = requests.get(m[0]['xls_candidate_url'], timeout=30)
    r.raise_for_status()
    if not r.content.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
        raise ValueError('same-stem XLS is unavailable or invalid')
    book = xlrd.open_workbook(file_contents=r.content, formatting_info=True)
    return {'source': '陕西省统计局《陕西统计年鉴2017》', 'edition': 2017, 'id': table_id, 'title': m[0]['title'], 'source_url': m[0]['xls_candidate_url'], 'image_url': m[0]['image_url'], 'sheets': [{'name': s.name, 'rows': [s.row_values(i) for i in range(s.nrows)], 'merged_cells': [list(x) for x in s.merged_cells]} for s in book.sheets()], 'merged_cells_convention': '[row_start,row_end_exclusive,col_start,col_end_exclusive]'}
