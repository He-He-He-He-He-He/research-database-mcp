"""Fujian statistical yearbook official HTML tables, 2016–2022 editions."""
import release_runtime
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
BASE = 'https://tjj.fujian.gov.cn/tongjinianjian/'

def _get(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.content

def catalog(year, keyword=''):
    if isinstance(year, bool) or not isinstance(year, int) or year not in range(2016, 2023):
        raise ValueError('available editions: 2016–2022')
    base = BASE + f'dz{year}/'
    soup = BeautifulSoup(_get(base + 'contents-cn.htm'), 'html.parser')
    items = []
    for a in soup.select('a[href]'):
        path = a['href']
        if not re.fullmatch('\\./cn(?:-en)?/html/[A-Za-z0-9_-]+\\.htm', path):
            continue
        title = ' '.join(a.get_text(' ', strip=True).split())
        match = re.match('^(\\d+-\\d+[A-Za-z]?)\\b', title)
        if match and keyword in title:
            items.append({'id': match.group(1), 'title': title, 'url': urljoin(base, path)})
    if not items and (not keyword):
        raise ValueError('yearbook catalog format changed')
    return items

def table(year, table_id):
    matches = [item for item in catalog(year) if item['id'] == table_id]
    if len(matches) != 1:
        raise ValueError('table ID missing or ambiguous')
    item = matches[0]
    soup = BeautifulSoup(_get(item['url']), 'html.parser')
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
    return {'source': f'福建省统计局《福建统计年鉴{year}》', 'edition': year, 'source_url': item['url'], 'catalog_url': BASE + f'dz{year}/contents-cn.htm', 'id': item['id'], 'title': item['title'], 'tables': tables, 'text': soup.get_text('\n', strip=True)}
