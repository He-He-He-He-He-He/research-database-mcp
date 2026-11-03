"""Official 2023 Ningbo Statistical Yearbook numbered Excel tables."""
import release_runtime
import re
import sys
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
try:
    import xlrd
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
    import xlrd
BASE = 'https://zjjcmspublic.oss-cn-hangzhou-zwynet-d01-a.internet.cloud.zj.gov.cn/jcms_files/jcms1/web3426/site/nbtjj/tjnj1/20232/'
INDEX = BASE + 'lefte.htm'

def _get(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.content

def catalog(keyword=''):
    soup = BeautifulSoup(_get(INDEX), 'html.parser')
    items = []
    for a in soup.select('a[href]'):
        href = a['href']
        match = re.fullmatch('excel/(\\d+-\\d+)\\.xls', href, re.I)
        title = ' '.join(a.get_text(' ', strip=True).split())
        if match and keyword in title:
            items.append({'id': match.group(1), 'title': title, 'url': urljoin(BASE, href)})
    if not items and (not keyword):
        raise ValueError('catalog format changed')
    return items

def table(table_id):
    items = [item for item in catalog() if item['id'] == table_id]
    if len(items) != 1:
        raise ValueError('table ID missing or ambiguous')
    item = items[0]
    book = xlrd.open_workbook(file_contents=_get(item['url']), formatting_info=True)
    sheets = []
    for sh in book.sheets():
        sheets.append({'name': sh.name, 'rows': [sh.row_values(i) for i in range(sh.nrows)], 'merged_cells': sh.merged_cells})
    return {'source': '宁波市统计局《宁波统计年鉴-2023》', 'catalog_url': INDEX, 'source_url': item['url'], 'id': item['id'], 'title': item['title'], 'sheets': sheets}
