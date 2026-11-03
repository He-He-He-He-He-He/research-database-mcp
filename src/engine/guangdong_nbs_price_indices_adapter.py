"""Official Guangdong NBS survey office CPI and producer price tables."""
import release_runtime
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
ROOT = 'https://gdzd.stats.gov.cn/dcsj/wjzs/'
KINDS = {'cpi': 'jmxfflzs', 'ppi_output': 'gysczccjgzs', 'ppi_input': 'gysczgjjgzs'}

def catalog(kind, page=0):
    if kind not in KINDS:
        raise ValueError('kind must be cpi, ppi_output, or ppi_input')
    if isinstance(page, bool) or not isinstance(page, int) or (not 0 <= page <= 100):
        raise ValueError('page must be an integer from 0 to 100')
    base = ROOT + KINDS[kind] + '/'
    url = base + ('index.html' if page == 0 else f'index_{page}.html')
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    out = []
    for a in s.select('a[href]'):
        p = a['href'].strip()
        title = ' '.join(a.get_text(' ', strip=True).split())
        if re.fullmatch('\\./\\d{6}/t\\d+_\\d+\\.html', p) and re.match('^\\d{4}年\\d{1,2}月', title):
            out.append({'title': title, 'url': urljoin(base, p), 'kind': kind})
    return {'source': '国家统计局广东调查总队', 'catalog_url': url, 'kind': kind, 'page': page, 'items': out}

def table(kind, url):
    if kind not in KINDS:
        raise ValueError('unknown kind')
    pattern = re.escape(ROOT + KINDS[kind] + '/') + '\\d{6}/t\\d+_\\d+\\.html'
    if not isinstance(url, str) or not re.fullmatch(pattern, url):
        raise ValueError('URL must be an official article for this kind')
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
        raise ValueError('no table found')
    title = s.find('h1') or s.find('h2') or s.find('title')
    return {'source': '国家统计局广东调查总队', 'kind': kind, 'url': url, 'title': title.get_text(' ', strip=True) if title else '', 'tables': tables}
