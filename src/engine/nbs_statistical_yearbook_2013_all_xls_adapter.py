"""National Bureau of Statistics China Statistical Yearbook 2013 XLS tables."""
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
BASE = 'https://www.stats.gov.cn/sj/ndsj/2013/'

def catalog(keyword=''):
    url = BASE + 'lefte.htm'
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content.decode('gb18030'), 'html.parser')
    items = []
    seen = set()
    for a in s.select('a[href]'):
        path = a['href'].replace('\\', '/').strip()
        title = ' '.join(a.get_text(' ', strip=True).split())
        if re.fullmatch('html/[A-Za-z0-9_-]+\\.xls', path, re.I) and title and (path.lower() not in seen):
            seen.add(path.lower())
            if keyword in title:
                items.append({'id': path, 'title': title, 'url': urljoin(BASE, path)})
    if not seen:
        raise ValueError('catalog missing or changed')
    return {'source': '国家统计局', 'book': '中国统计年鉴2013', 'catalog_url': url, 'total': len(seen), 'matched_count': len(items), 'count_note': 'total 为全目录数，matched_count 为标题关键词命中数；未命中不代表正文无相关内容。', 'items': items}

def table(table_id):
    if not isinstance(table_id, str):
        raise ValueError('table ID must be from catalog')
    c = catalog()
    items = [x for x in c['items'] if x['id'] == table_id]
    if len(items) != 1:
        raise ValueError('unknown or ambiguous table ID')
    item = items[0]
    r = requests.get(item['url'], timeout=30)
    r.raise_for_status()
    if not r.content.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
        raise ValueError('response is not XLS')
    w = xlrd.open_workbook(file_contents=r.content, formatting_info=True)
    return {'source': '国家统计局', 'book': '中国统计年鉴2013', 'id': table_id, 'title': item['title'], 'source_url': item['url'], 'sheets': [{'name': s.name, 'rows': [s.row_values(i) for i in range(s.nrows)], 'merged_cells': [list(x) for x in s.merged_cells]} for s in w.sheets()], 'merged_cells_convention': '[row_start,row_end_exclusive,col_start,col_end_exclusive]'}
