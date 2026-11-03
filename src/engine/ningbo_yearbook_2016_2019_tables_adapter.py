"""Ningbo 2016–2019 official yearbook tables, XLS companions to catalog images."""
import release_runtime
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
try:
    import xlrd
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
    import xlrd
BASE = 'https://zjjcmspublic.oss-cn-hangzhou-zwynet-d01-a.internet.cloud.zj.gov.cn/jcms_files/jcms1/web3426/site/nbtjj/tjnj1/'
INDEXES = {y: BASE + f'{y}nbnj/zk/left.htm' for y in range(2016, 2020)}

def _get(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.content

def catalog(year, keyword=''):
    if isinstance(year, bool) or year not in INDEXES:
        raise ValueError('available editions: 2016–2019')
    index = INDEXES[year]
    soup = BeautifulSoup(_get(index), 'html.parser')
    items = []
    for a in soup.select('a[href]'):
        title = ' '.join(a.get_text(' ', strip=True).split())
        m = re.match('^表(\\d+-\\d+)\\s', title)
        image = urljoin(index, a['href'])
        u = urlparse(image)
        if m and image.startswith(BASE) and re.fullmatch('(?:.*/)?html/\\d{2}-\\d{2}\\.jpg', u.path, re.I) and (keyword in title):
            items.append({'id': m.group(1), 'title': title, 'catalog_image_url': image, 'xls_url': image[:-4] + '.xls'})
    if not items and (not keyword):
        raise ValueError('official catalog missing')
    return items

def table(year, table_id):
    matches = [x for x in catalog(year) if x['id'] == table_id]
    if len(matches) != 1:
        raise ValueError('table missing or ambiguous')
    item = matches[0]
    raw = _get(item['xls_url'])
    if not raw.startswith(bytes.fromhex('d0cf11e0a1b11ae1')):
        raise ValueError('XLS companion missing or not Excel')
    book = xlrd.open_workbook(file_contents=raw, formatting_info=True)
    sheets = [{'name': s.name, 'rows': [s.row_values(i) for i in range(s.nrows)], 'merged_cells': s.merged_cells} for s in book.sheets()]
    return {'source': f'宁波市统计局《宁波统计年鉴{year}》', 'edition': year, 'id': table_id, 'title': item['title'], 'source_url': item['xls_url'], 'catalog_image_url': item['catalog_image_url'], 'catalog_url': INDEXES[year], 'sheets': sheets}
