"""Official Fujian commerce department national and provincial trade tables."""
import release_runtime
import re
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
ROOT = 'https://swt.fujian.gov.cn/'
INDEX = ROOT + 'xxgk/tjxx/hwmy/'
PATH = re.compile('/(?:xxgk/tjxx/hwmy|xxgk/jgzn/jgcs/dwmyc/tjxx|jgzn/jgcs/dwmyc/tjxx)/\\d{6}/t\\d+_\\d+\\.htm')

def catalog(page=0):
    if isinstance(page, bool) or not isinstance(page, int) or (not 0 <= page <= 100):
        raise ValueError('page must be 0–100')
    url = INDEX + ('index.htm' if page == 0 else f'index_{page}.htm')
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    out = []
    for a in s.select('a[href]'):
        title = ' '.join(a.get_text(' ', strip=True).split())
        link = urljoin(url, a['href'])
        p = urlsplit(link)
        if '全国与我省进出口总值' in title and p.scheme == 'https' and (p.netloc == 'swt.fujian.gov.cn') and PATH.fullmatch(p.path):
            out.append({'title': title, 'url': link})
    return {'source': '福建省商务厅', 'catalog_url': url, 'page': page, 'items': out}

def table(url):
    if not isinstance(url, str):
        raise ValueError('URL must be a string')
    p = urlsplit(url)
    if p.scheme != 'https' or p.netloc != 'swt.fujian.gov.cn' or (not PATH.fullmatch(p.path)) or p.query or p.fragment:
        raise ValueError('URL must be an official trade article')
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    h = s.find('h1') or s.find('h2') or s.find('title')
    title = h.get_text(' ', strip=True) if h else ''
    if '全国与我省进出口总值' not in title:
        raise ValueError('article is not a national and Fujian trade table')
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
    return {'source': '福建省商务厅', 'url': url, 'title': title, 'tables': tables}
