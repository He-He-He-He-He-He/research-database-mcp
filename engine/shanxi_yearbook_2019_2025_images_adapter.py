"""Official Shanxi yearbook image/PDF originals, editions 2019–2025."""
import release_runtime
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
ROOT = 'https://tjj.shanxi.gov.cn/tjsj/tjnj/'

def _base(year):
    if isinstance(year, bool) or not isinstance(year, int) or year not in range(2019, 2026):
        raise ValueError('available editions: 2019–2025')
    return ROOT + f'nj{year}/zk/'

def catalog(year, keyword=''):
    base = _base(year)
    r = requests.get(base + 'left.htm', timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, 'html.parser')
    out = []
    for a in soup.select('a[href]'):
        path = a['href'].strip()
        title = ' '.join(a.get_text(' ', strip=True).split())
        if title and re.fullmatch('html/[A-Za-z0-9_-]+\\.(?:jpg|pdf)', path, re.I) and (keyword in title):
            out.append({'edition': year, 'source': f'山西省统计局《山西统计年鉴{year}》', 'title': title, 'path': path, 'url': urljoin(base, path), 'catalog_url': base + 'left.htm'})
    if not out and (not keyword):
        raise ValueError('catalog missing or changed')
    return out

def document(year, path):
    matches = [x for x in catalog(year) if x['path'] == path]
    if not matches:
        raise ValueError('path is not in the edition catalog')
    r = requests.get(matches[0]['url'], timeout=60)
    r.raise_for_status()
    kind = 'application/pdf' if path.lower().endswith('.pdf') else 'image/jpeg'
    if kind == 'application/pdf' and (not r.content.startswith(b'%PDF-')) or (kind == 'image/jpeg' and (not r.content.startswith(b'\xff\xd8\xff'))):
        raise ValueError('unexpected document type')
    return {**matches[0], 'content_type': kind, 'content': r.content}
