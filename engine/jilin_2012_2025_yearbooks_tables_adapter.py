"""Official Jilin statistical yearbooks 2012–2025 HTML tables."""
import release_runtime
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
ROOT = 'https://tjj.jl.gov.cn/tjsj/tjnj/'

def _base(year):
    if isinstance(year, bool) or not isinstance(year, int) or (not 2012 <= year <= 2025):
        raise ValueError('year must be 2012–2025')
    return f'{ROOT}{year}/'

def catalog(year, keyword=''):
    base = _base(year)
    url = base + 'ml/njmlc.htm'
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    if year <= 2015:
        s = BeautifulSoup(r.content.decode('gb18030'), 'html.parser')
    else:
        s = BeautifulSoup(r.content, 'html.parser')
    out = []
    for a in s.select('a[href]'):
        p = a['href'].strip()
        title = ' '.join(a.get_text(' ', strip=True).split())
        if re.fullmatch('\\.\\./(?:html|' + str(year) + ')/[A-Za-z0-9_-]+\\.html?', p, re.I) and title and (keyword in title):
            out.append({'id': p[3:], 'title': title, 'url': urljoin(url, p)})
    if not out and (not keyword):
        raise ValueError('missing or changed catalog')
    return {'source': '吉林省统计局', 'yearbook': year, 'catalog_url': url, 'items': out}

def table(year, table_id):
    if not isinstance(table_id, str):
        raise ValueError('table ID must come from catalog')
    c = catalog(year)
    m = [i for i in c['items'] if i['id'] == table_id]
    if len(m) != 1:
        raise ValueError('unknown or ambiguous table ID')
    r = requests.get(m[0]['url'], timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    tables = []
    for t in s.find_all('table'):
        rows = []
        for tr in t.find_all('tr'):
            cells = [{'text': x.get_text(' ', strip=True), 'rowspan': int(x.get('rowspan', 1)), 'colspan': int(x.get('colspan', 1))} for x in tr.find_all(['td', 'th'], recursive=False)]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    if not tables:
        raise ValueError('no HTML table')
    return {'source': '吉林省统计局', 'yearbook': year, 'id': table_id, 'title': m[0]['title'], 'url': m[0]['url'], 'tables': tables, 'page_text': s.get_text('\n', strip=True)}
