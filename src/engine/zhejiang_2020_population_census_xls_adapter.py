"""Zhejiang 2020 population census yearbook XLS tables hosted on government cloud."""
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
BASE = 'https://zjjcmspublic.oss-cn-hangzhou-zwynet-d01-a.internet.cloud.zj.gov.cn/jcms_files/jcms1/web3077/site/flash/tjj/Reports1/浙江人普2020光盘/'

def catalog(keyword=''):
    r = requests.get(BASE + 'lefte.htm', timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    out = []
    for a in s.select('a[href]'):
        p = a['href'].strip()
        title = ' '.join(a.get_text(' ', strip=True).split())
        if re.fullmatch('(?:[A-Za-z0-9_-]+/)*html/[A-Za-z0-9_-]+\\.xls', p, re.I) and title and (keyword in title):
            out.append({'id': p[:-4], 'title': title, 'url': urljoin(BASE, p)})
    if not out and (not keyword):
        raise ValueError('catalog missing or changed')
    return {'source': '浙江省人口普查年鉴—2020', 'catalog_url': BASE + 'lefte.htm', 'items': out}

def table(table_id):
    if not isinstance(table_id, str) or not re.fullmatch('(?:[A-Za-z0-9_-]+/)*html/[A-Za-z0-9_-]+', table_id):
        raise ValueError('invalid table ID')
    c = catalog()
    m = [x for x in c['items'] if x['id'] == table_id]
    if len(m) != 1:
        raise ValueError('table ID missing or ambiguous')
    r = requests.get(m[0]['url'], timeout=30)
    r.raise_for_status()
    if not r.content.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
        raise ValueError('response is not XLS')
    w = xlrd.open_workbook(file_contents=r.content, formatting_info=True)
    return {'source': c['source'], 'id': table_id, 'title': m[0]['title'], 'source_url': m[0]['url'], 'sheets': [{'name': s.name, 'rows': [s.row_values(i) for i in range(s.nrows)], 'merged_cells': [list(x) for x in s.merged_cells]} for s in w.sheets()], 'merged_cells_convention': '[row_start,row_end_exclusive,col_start,col_end_exclusive]'}
