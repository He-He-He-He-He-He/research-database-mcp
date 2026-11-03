"""Ningbo official 2007 statistical yearbook HTML tables."""
import release_runtime
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
BASE = 'https://zjjcmspublic.oss-cn-hangzhou-zwynet-d01-a.internet.cloud.zj.gov.cn/jcms_files/jcms1/web3426/site/nbtjj/tjnj1/'

def _index(year):
    if isinstance(year, bool) or not isinstance(year, int) or year != 2007:
        raise ValueError('available edition: 2007')
    return BASE + f'{year}nbnj/left.htm'

def _get(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.content

def catalog(year, keyword=''):
    index = _index(year)
    soup = BeautifulSoup(_get(index), 'html.parser')
    out = []
    for a in soup.select('a[href]'):
        title = ' '.join(a.get_text(' ', strip=True).split())
        m = re.match('^表(\\d+-\\d+)\\s', title)
        path = a['href']
        if m and re.fullmatch('htm/[A-Za-z0-9_-]+\\.htm', path, re.I) and (keyword in title):
            out.append({'id': m.group(1), 'title': title, 'url': urljoin(index, path)})
    if not out and (not keyword):
        raise ValueError('official catalog missing')
    return out

def table(year, table_id):
    items = [x for x in catalog(year) if x['id'] == table_id]
    if len(items) != 1:
        raise ValueError('table missing or ambiguous')
    item = items[0]
    soup = BeautifulSoup(_get(item['url']), 'html.parser')
    tables = []
    for tab in soup.find_all('table'):
        rows = []
        for tr in tab.find_all('tr'):
            cells = [{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    if not tables:
        raise ValueError('official table missing')
    return {'source': f'宁波市统计局《宁波统计年鉴{year}》', 'edition': year, 'id': table_id, 'title': item['title'], 'source_url': item['url'], 'catalog_url': _index(year), 'tables': tables, 'text': soup.get_text('\n', strip=True)}
