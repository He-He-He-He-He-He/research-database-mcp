"""Fujian statistical bureau GDP preliminary accounting release tables."""
import release_runtime
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
ROOT = 'https://tjj.fujian.gov.cn/xxgk/jdsj/'

def catalog(page=0, keyword=''):
    if isinstance(page, bool) or not isinstance(page, int) or (not 0 <= page <= 100):
        raise ValueError('page must be 0–100')
    url = ROOT + ('index.htm' if page == 0 else f'index_{page}.htm')
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    out = []
    seen = set()
    for a in s.select('a[href]'):
        p = a['href'].strip()
        title = ' '.join(a.get_text(' ', strip=True).split())
        if re.fullmatch('\\./\\d{6}/t\\d+_\\d+\\.htm', p) and '地区生产总值' in title and (keyword in title):
            link = urljoin(ROOT, p)
            if link not in seen:
                out.append({'title': title, 'url': link})
                seen.add(link)
    return {'source': '福建省统计局', 'catalog_url': url, 'page': page, 'items': out}

def release(url):
    if not isinstance(url, str) or not re.fullmatch(re.escape(ROOT) + '\\d{6}/t\\d+_\\d+\\.htm', url):
        raise ValueError('invalid official release URL')
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    body = s.select_one('.article_content')
    if body is None:
        raise ValueError('article content missing')
    heading = s.select_one('.article_title')
    title = heading.get_text(' ', strip=True) if heading else s.title.get_text(' ', strip=True) if s.title else ''
    text = body.get_text('\n', strip=True)
    if '地区生产总值' not in title + ' ' + text:
        raise ValueError('not a GDP release')
    tables = []
    for t in body.find_all('table'):
        rows = []
        for tr in t.find_all('tr'):
            cells = [{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    if not tables:
        raise ValueError('no HTML table')
    return {'source': '福建省统计局', 'url': url, 'title': title, 'article_text': text, 'tables': tables}
