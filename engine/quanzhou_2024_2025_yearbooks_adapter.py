"""泉州市统计局2024、2025统计年鉴公开 HTML 原表。"""
import release_runtime
import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
ROOT = 'https://tjj.quanzhou.gov.cn/tsys/UpLoadFiles/43sjfb/129ndsj/'

def _base(year):
    if isinstance(year, bool) or year not in (2024, 2025):
        raise ValueError('仅支持年鉴版次 2024、2025')
    return ROOT + f'qztjnj{year}/'

def _fetch(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.content, 'html.parser')

def catalog(year, keyword=''):
    base = _base(year)
    s = _fetch(base + 'contents-cn.htm')
    items = []
    for a in s.select('a[href]'):
        href = a['href'].strip()
        title = ' '.join(a.get_text(' ', strip=True).split())
        if re.fullmatch('\\./cn/html/[A-Za-z0-9_-]+\\.html?', href) and title and (keyword in title):
            items.append({'id': href.rsplit('/', 1)[-1], 'title': title, 'url': urljoin(base, href)})
    if not items and (not keyword):
        raise ValueError('目录缺失或网页结构已改变')
    return {'source': f'泉州市统计局《泉州统计年鉴{year}》', 'edition': year, 'catalog_url': base + 'contents-cn.htm', 'items': items}

def table(year, table_id):
    matches = [i for i in catalog(year)['items'] if i['id'] == table_id]
    if len(matches) != 1:
        raise ValueError('表 ID 不存在或不唯一')
    item = matches[0]
    s = _fetch(item['url'])
    tables = []
    for table in s.find_all('table'):
        rows = []
        for tr in table.find_all('tr'):
            cells = []
            for cell in tr.find_all(['td', 'th'], recursive=False):
                cells.append({'text': ' '.join(cell.get_text(' ', strip=True).split()), 'rowspan': int(cell.get('rowspan', 1)), 'colspan': int(cell.get('colspan', 1))})
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    if not tables:
        raise ValueError('该目录项无可解析 HTML 表格，可能是说明或图片')
    return {'source': f'泉州市统计局《泉州统计年鉴{year}》', 'edition': year, 'title': item['title'], 'source_url': item['url'], 'tables': tables, 'note': '按 HTML 原始单元格保留文本与跨行跨列；版次不是数据年份，具体年份、单位与口径以原表为准。'}
