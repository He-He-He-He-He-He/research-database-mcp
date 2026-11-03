"""Official Fujian statistical yearbook HTML catalogs and tables, editions 2000–2010."""
import release_runtime
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
BASE = 'https://tjj.fujian.gov.cn/tongjinianjian/'

def _base(year):
    if isinstance(year, bool) or not isinstance(year, int) or year not in range(2000, 2011):
        raise ValueError('available editions: 2000–2010')
    return BASE + f'dz{year % 100:02d}/'

def _soup(url, year):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    content = r.content.decode('gb18030', errors='replace') if year <= 2006 else r.content
    return BeautifulSoup(content, 'html.parser')

def catalog(year, keyword=''):
    base = _base(year)
    url = base + ('contents-cn.htm' if year >= 2009 else 'njml.htm')
    items = []
    for a in _soup(url, year).select('a[href]'):
        path = a['href']
        if not re.fullmatch('(?:\\./)?(?:nj200[01]|html|cn/html)/[A-Za-z0-9_-]+\\.htm', path):
            continue
        title = ' '.join(a.get_text(' ', strip=True).split())
        match = re.match('^(\\d+-\\d+(?:续\\d*)?)', title)
        if match and keyword in title:
            items.append({'id': match.group(1), 'title': title, 'url': urljoin(base, path)})
    if not items and (not keyword):
        raise ValueError('yearbook catalog format changed')
    return items

def table(year, table_id):
    matches = [i for i in catalog(year) if i['id'] == table_id]
    if len(matches) != 1:
        raise ValueError('table ID missing or ambiguous; inspect catalog')
    item = matches[0]
    soup = _soup(item['url'], year)
    tables = []
    for t in soup.find_all('table'):
        rows = []
        for tr in t.find_all('tr'):
            cells = [{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    if not tables:
        raise ValueError('table missing')
    return {'source': f'福建省统计局《福建统计年鉴{year}》', 'edition': year, 'source_url': item['url'], 'catalog_url': _base(year) + ('contents-cn.htm' if year >= 2009 else 'njml.htm'), 'id': item['id'], 'title': item['title'], 'tables': tables, 'text': soup.get_text('\n', strip=True)}
