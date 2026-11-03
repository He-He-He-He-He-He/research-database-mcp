"""Current Liaoning Bureau of Statistics monthly economic HTML tables."""
import release_runtime
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
ROOT = 'https://tjj.ln.gov.cn/'
INDEX = ROOT + 'tjj/tjsj/sjfb/ydsj/'
PATH = re.compile('/tjj/tjsj/sjfb/ydsj/\\d{19}/index\\.shtml')

def catalog(keyword=''):
    r = requests.get(INDEX, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    out = []
    for a in s.select('a[href]'):
        p = a['href'].strip()
        title = ' '.join(a.get_text(' ', strip=True).split())
        if PATH.fullmatch(p) and re.match('^\\d{4}年', title) and (keyword in title):
            out.append({'title': title, 'url': urljoin(ROOT, p)})
    if not out and (not keyword):
        raise ValueError('monthly catalog missing or changed')
    return {'source': '辽宁省统计局', 'catalog_url': INDEX, 'scope': '当前首页列表', 'items': out}

def table(url):
    if not isinstance(url, str) or not url.startswith(ROOT) or (not PATH.fullmatch('/' + url[len(ROOT):])):
        raise ValueError('URL must be an official monthly data article')
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    out = []
    for t in s.find_all('table'):
        rows = []
        for tr in t.find_all('tr'):
            cells = [{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
            if cells:
                rows.append(cells)
        if rows:
            out.append(rows)
    if not out:
        raise ValueError('no HTML table found')
    return {'source': '辽宁省统计局', 'url': url, 'title': s.title.get_text(' ', strip=True) if s.title else '', 'tables': out}
