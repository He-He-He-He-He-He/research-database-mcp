"""Current statistics tables linked by the Jiangsu NBS survey office homepage."""
import release_runtime
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
ROOT = 'https://jszd.stats.gov.cn/'
PATH = re.compile('/TrueCMS//gjtjjjsdczd/[A-Za-z0-9]+/content/[0-9a-fA-F-]{36}\\.html')

def catalog(keyword=''):
    r = requests.get(ROOT, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    t = s.select_one('table.table_dcsj')
    if t is None:
        raise ValueError('statistics table missing or changed')
    out = []
    for tr in t.select('tr'):
        cells = tr.find_all('td', recursive=False)
        if not cells:
            continue
        category = ' '.join(cells[0].get_text(' ', strip=True).split())
        for a in tr.select('a[href]'):
            href = a['href']
            if PATH.fullmatch(href) and keyword in category:
                out.append({'category': category, 'period': a.get_text(' ', strip=True), 'url': urljoin(ROOT, href)})
    return {'source': '国家统计局江苏调查总队', 'catalog_url': ROOT, 'scope': '首页当前链接', 'items': out}

def table(url):
    if not isinstance(url, str) or not url.startswith(ROOT):
        raise ValueError('invalid official URL')
    path = '/' + url[len(ROOT):]
    if not PATH.fullmatch(path):
        raise ValueError('URL is not a statistics article')
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    tables = []
    for t in s.find_all('table'):
        rows = []
        for tr in t.find_all('tr'):
            cells = [{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    if not tables:
        raise ValueError('no HTML table found')
    return {'source': '国家统计局江苏调查总队', 'url': url, 'title': s.title.get_text(' ', strip=True) if s.title else '', 'tables': tables}
