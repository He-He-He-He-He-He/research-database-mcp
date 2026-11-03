"""Zhejiang 2020 population census yearbook originals hosted by Zhejiang government cloud."""
import release_runtime
from urllib.parse import urljoin
import re
import requests
from bs4 import BeautifulSoup
BASE = 'https://zjjcmspublic.oss-cn-hangzhou-zwynet-d01-a.internet.cloud.zj.gov.cn/jcms_files/jcms1/web3077/site/flash/tjj/Reports1/浙江人普2020光盘/'

def catalog(keyword=''):
    r = requests.get(BASE + 'left.htm', timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, 'html.parser')
    out = []
    for a in soup.select('a[href]'):
        p = a['href'].strip()
        if not re.fullmatch('(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_-]+\\.(?:jpg|pdf)', p, re.I):
            continue
        title = ' '.join(a.get_text(' ', strip=True).split())
        if title and keyword in title:
            out.append({'title': title, 'path': p, 'url': urljoin(BASE, p), 'source': '浙江省人口普查年鉴—2020', 'catalog_url': BASE + 'left.htm'})
    if not out and (not keyword):
        raise ValueError('catalog empty or changed')
    return out

def document(path):
    items = [x for x in catalog() if x['path'] == path]
    if not items:
        raise ValueError('path is not in the source catalog')
    r = requests.get(items[0]['url'], timeout=45)
    r.raise_for_status()
    kind = 'application/pdf' if path.lower().endswith('.pdf') else 'image/jpeg'
    if kind == 'image/jpeg' and (not r.content.startswith(b'\xff\xd8\xff')) or (kind == 'application/pdf' and (not r.content.startswith(b'%PDF-'))):
        raise ValueError('response is not an image or PDF')
    return {**items[0], 'content_type': kind, 'content': r.content}
