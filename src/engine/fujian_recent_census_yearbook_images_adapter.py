"""Official Fujian yearbook and census indexed image/PDF originals."""
import release_runtime
from urllib.parse import urljoin
import re
import requests
from bs4 import BeautifulSoup
ROOT = 'https://tjj.fujian.gov.cn/tongjinianjian/'
BOOKS = {'2023': ('福建统计年鉴2023', 'dz2023/'), '2024': ('福建统计年鉴2024', 'dz2024/'), '2025': ('福建统计年鉴2025', 'dz2025/zk/'), 'census2020': ('福建省人口普查年鉴2020', 'rk2020/'), 'economic_census2023': ('福建经济普查年鉴2023', 'jp2023/')}

def catalog(book, keyword=''):
    if book not in BOOKS:
        raise ValueError('unknown book; use BOOKS keys')
    name, path = BOOKS[book]
    base = ROOT + path
    r = requests.get(base + 'left.htm', timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, 'html.parser')
    result = []
    for a in soup.select('a[href]'):
        ref = a['href'].strip()
        if not re.fullmatch('(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_-]+\\.(?:jpg|pdf)', ref, re.I):
            continue
        title = ' '.join(a.get_text(' ', strip=True).split())
        if title and keyword in title:
            result.append({'book': book, 'source': name, 'title': title, 'path': ref, 'url': urljoin(base, ref), 'catalog_url': base + 'left.htm'})
    if not result and (not keyword):
        raise ValueError('catalog empty or changed')
    return result

def document(book, path):
    matches = [x for x in catalog(book) if x['path'] == path]
    if not matches:
        raise ValueError('path is not an indexed document')
    r = requests.get(matches[0]['url'], timeout=45)
    r.raise_for_status()
    expected = 'application/pdf' if path.lower().endswith('.pdf') else 'image/jpeg'
    if expected == 'image/jpeg' and (not r.content.startswith(b'\xff\xd8\xff')) or (expected == 'application/pdf' and (not r.content.startswith(b'%PDF-'))):
        raise ValueError('response is not the expected image or PDF')
    return {**matches[0], 'content_type': expected, 'content': r.content}
