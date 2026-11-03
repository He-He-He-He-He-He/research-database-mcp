"""National Bureau of Statistics 2020 population census XLS tables."""
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
BASE = 'https://www.stats.gov.cn/sj/pcsj/rkpc/7rp/zk/'

def catalog(keyword=''):
    url = BASE + 'lefte.htm'
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content.decode('gb18030'), 'html.parser')
    items = []
    seen = set()
    part = None
    for a in s.select('a[href]'):
        path = a['href'].replace('\\', '/').strip()
        title = ' '.join(a.get_text(' ', strip=True).split())
        if '第一部分' in title:
            part = '全部数据资料'
        elif '第二部分' in title:
            part = '长表数据资料'
        elif '第三部分' in title:
            part = '附录'
        if re.fullmatch('html/[A-Za-z0-9_-]+\\.xls', path, re.I) and title and (path.lower() not in seen):
            seen.add(path.lower())
            if keyword in title:
                items.append({'id': path, 'title': title, 'part': part, 'url': urljoin(BASE, path)})
    if not seen:
        raise ValueError('catalog missing or changed')
    return {'source': '国家统计局', 'book': '中国人口普查年鉴2020', 'catalog_url': url, 'total': len(seen), 'matched_count': len(items), 'count_note': 'total 为全目录表数，matched_count 为按标题关键词匹配的表数；标题未命中不代表表格内容无相关数据。', 'items': items}

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
    return {'source': '国家统计局', 'book': '中国人口普查年鉴2020', 'id': table_id, 'title': item['title'], 'part': item['part'], 'source_url': item['url'], 'sheets': [{'name': s.name, 'rows': [s.row_values(i) for i in range(s.nrows)], 'merged_cells': [list(x) for x in s.merged_cells]} for s in w.sheets()], 'merged_cells_convention': '[row_start,row_end_exclusive,col_start,col_end_exclusive]'}
