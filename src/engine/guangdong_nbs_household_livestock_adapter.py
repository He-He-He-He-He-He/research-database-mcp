"""Official Guangdong survey office household incomes and livestock tables."""
import release_runtime
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
ROOT = 'https://gdzd.stats.gov.cn/dcsj/'
KINDS = {'urban': 'czjmsz', 'rural': 'ncjmsz', 'livestock': 'nysc/cmysc'}

def catalog(kind, page=0):
    if kind not in KINDS:
        raise ValueError('kind must be urban, rural, or livestock')
    if isinstance(page, bool) or not isinstance(page, int) or (not 0 <= page <= 100):
        raise ValueError('page must be 0–100')
    base = ROOT + KINDS[kind] + '/'
    url = base + ('index.html' if page == 0 else f'index_{page}.html')
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    items = []
    for a in s.select('a[href]'):
        p = a['href'].strip()
        title = ' '.join(a.get_text(' ', strip=True).split())
        if re.fullmatch('\\./\\d{6}/t\\d+_\\d+\\.html', p) and re.match('^\\d{4}年', title):
            items.append({'kind': kind, 'title': title, 'url': urljoin(base, p)})
    return {'source': '国家统计局广东调查总队', 'kind': kind, 'page': page, 'catalog_url': url, 'items': items}

def table(kind, url):
    if kind not in KINDS:
        raise ValueError('unknown kind')
    if not isinstance(url, str) or not re.fullmatch(re.escape(ROOT + KINDS[kind] + '/') + '\\d{6}/t\\d+_\\d+\\.html', url):
        raise ValueError('URL must be an official article of the selected category')
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
        raise ValueError('article contains no HTML table')
    h = s.find('h1') or s.find('h2') or s.find('title')
    return {'source': '国家统计局广东调查总队', 'kind': kind, 'url': url, 'title': h.get_text(' ', strip=True) if h else '', 'tables': tables}
