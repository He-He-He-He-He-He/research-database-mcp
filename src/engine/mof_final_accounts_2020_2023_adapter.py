"""MOF 2020–2023 annual final accounts table catalogs and HTML tables."""
import release_runtime
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

def catalog(year, keyword=''):
    if year not in (2020, 2021, 2022, 2023):
        raise ValueError('available years: 2020–2023')
    if not isinstance(keyword, str):
        raise ValueError('keyword must be a string')
    url = f'https://yss.mof.gov.cn/{year}zyjs/'
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    items = []
    seen = set()
    for a in s.select('a[href]'):
        title = a.get_text(' ', strip=True)
        href = a['href']
        if '决算表' not in title or keyword not in title or (not href.startswith('./')):
            continue
        target = urljoin(url, href)
        if target not in seen:
            items.append({'title': title, 'url': target})
            seen.add(target)
    if not items and (not keyword):
        raise ValueError('no account tables found')
    return {'year': year, 'source': '财政部', 'source_url': url, 'items': items}

def table(year, url):
    match = next((x for x in catalog(year)['items'] if x['url'] == url), None)
    if match is None:
        raise ValueError('URL is not in the specified annual catalog')
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    tables = []
    for t in s.find_all('table'):
        rows = []
        for tr in t.find_all('tr'):
            cells = [{'text': c.get_text('', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    if not tables:
        raise ValueError('no HTML tables found')
    return {'year': year, 'source': '财政部', **match, 'tables': tables}
