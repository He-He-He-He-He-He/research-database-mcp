"""Official Zhejiang statistical yearbook 2019 HTML table catalog."""
import release_runtime
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
INDEX = 'https://zjjcmspublic.oss-cn-hangzhou-zwynet-d01-a.internet.cloud.zj.gov.cn/jcms_files/jcms1/web3077/site/flash/tjj/Reports1/2019年统计年鉴光盘20200706/html/cn/index.html'

def _get(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.content

def catalog(keyword=''):
    soup = BeautifulSoup(_get(INDEX), 'html.parser')
    items = []
    for a in soup.select('a[href]'):
        title = ' '.join(a.get_text(' ', strip=True).split())
        m = re.match('^(\\d+-\\d+[A-Za-z]?)\\s', title)
        path = a['href'].replace('\\', '/')
        if m and path.startswith('./') and path.endswith('.html') and ('..' not in path) and (keyword in title):
            items.append({'id': m.group(1), 'title': title, 'url': urljoin(INDEX, path)})
    if not items and (not keyword):
        raise ValueError('yearbook catalog format changed')
    return items

def table(table_id):
    matches = [x for x in catalog() if x['id'] == table_id]
    if len(matches) != 1:
        raise ValueError('table missing or ambiguous')
    item = matches[0]
    soup = BeautifulSoup(_get(item['url']), 'html.parser')
    t = soup.select_one('table.tableNormal')
    if not t:
        raise ValueError('official data table missing')
    rows = []
    for tr in t.find_all('tr', recursive=False):
        cells = [{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
        if cells:
            rows.append(cells)
    if not rows:
        raise ValueError('table rows missing')
    return {'source': '浙江省统计局《浙江统计年鉴-2019》', 'id': table_id, 'title': item['title'], 'source_url': item['url'], 'catalog_url': INDEX, 'rows': rows, 'text': soup.get_text('\n', strip=True)}
