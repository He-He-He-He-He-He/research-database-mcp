"""Inner Mongolia statistical office yearbook and 2020 census originals."""
import release_runtime
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
ROOT = 'https://tj.nmg.gov.cn/files_pub/content/PAGEPACK/'
BOOKS = {'2020': ('内蒙古统计年鉴2020', 'b85658190a3644f8b192e45f5221f2fa/zk/'), '2021': ('内蒙古统计年鉴2021', '83e5521da4e94d50ab45483b58e5fa7e/zk/'), '2023': ('内蒙古统计年鉴2023', '7f2e427b72bc45ec84f1773389947068/zk/'), 'census2020': ('内蒙古自治区人口普查年鉴2020', 'zk2020/')}

def catalog(book, keyword=''):
    if book not in BOOKS:
        raise ValueError('unknown book; see BOOKS')
    title, path = BOOKS[book]
    base = ROOT + path
    r = requests.get(base + 'left.htm', timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    out = []
    for a in s.select('a[href]'):
        p = a['href'].strip()
        name = ' '.join(a.get_text(' ', strip=True).split())
        if name and re.fullmatch('html/[A-Za-z0-9_-]+\\.(?:jpg|pdf)', p, re.I) and (keyword in name):
            out.append({'book': book, 'source': title, 'title': name, 'path': p, 'url': urljoin(base, p), 'catalog_url': base + 'left.htm'})
    if not out and (not keyword):
        raise ValueError('catalog missing or changed')
    return out

def document(book, path):
    items = [x for x in catalog(book) if x['path'] == path]
    if not items:
        raise ValueError('path is not in the selected catalog')
    r = requests.get(items[0]['url'], timeout=60)
    r.raise_for_status()
    kind = 'application/pdf' if path.lower().endswith('.pdf') else 'image/jpeg'
    if kind == 'application/pdf' and (not r.content.startswith(b'%PDF-')) or (kind == 'image/jpeg' and (not r.content.startswith(b'\xff\xd8\xff'))):
        raise ValueError('unexpected document type')
    return {**items[0], 'content_type': kind, 'content': r.content}
