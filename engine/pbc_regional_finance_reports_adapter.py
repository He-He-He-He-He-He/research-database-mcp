"""PBC regional financial reports: official annual regional PDF catalog and text."""
import release_runtime
import hashlib
from urllib.parse import urljoin, urlsplit
import requests, fitz
from bs4 import BeautifulSoup
PAGES = {2017: '3356630/42e128cd78514643bd814a4c0f78e5e8', 2018: '3564964/6b3cb21605e848e0a3c03921749304a4', 2019: '3861967/faee961cb8db4ed793d3c28801936dea', 2020: '4031309/89c22aeb443c452c85130af5876cc748', 2022: '4601166/dc38aaeda2834583a2cd4774b19e609e', 2023: '5127700/4b9891842eab4d7084309e8b8b03cd16', 2024: '5415491/73300d7391b844e5958cfd6fd8d18f59'}
ROOT = 'https://www.pbc.gov.cn/zhengcehuobisi/125207/125227/125960/126049/'

def _get(url, limit):
    with requests.get(url, stream=True, timeout=(10, 60), allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        data = bytearray()
        for chunk in r.iter_content(65536):
            data.extend(chunk)
            if len(data) > limit:
                raise ValueError('response too large')
    return bytes(data)

def catalog(year, keyword=''):
    if type(year) is not int or year not in PAGES:
        raise ValueError('available report editions: 2017–2020 and 2022–2024')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    url = ROOT + PAGES[year] + '/index.html'
    soup = BeautifulSoup(_get(url, 3000000), 'html.parser')
    items = []
    for a in soup.select('a[href]'):
        href = urljoin(url, a['href'])
        parts = urlsplit(href)
        title = ' '.join(a.get_text(' ', strip=True).split())
        if parts.scheme != 'https' or parts.hostname != 'www.pbc.gov.cn' or (not parts.path.lower().endswith('.pdf')) or (not title):
            continue
        if keyword in title:
            items.append({'id': parts.path.rsplit('/', 1)[-1][:-4], 'title': title, 'url': href})
    if not items and (not keyword):
        raise ValueError('official PDF catalog missing')
    return {'source': f'中国人民银行中国区域金融运行报告（{year}）官方附件目录', 'edition': year, 'source_url': url, 'count': len(items), 'items': items, 'note': '报告年份不是自动代表同一统计年份；地方报告常为摘要，内容及数据口径请看各PDF。'}

def detail(year, doc_id, page=1):
    if not isinstance(doc_id, str) or not doc_id.isdigit() or len(doc_id) > 30:
        raise ValueError('invalid document id')
    matches = [x for x in catalog(year)['items'] if x['id'] == doc_id]
    if len(matches) != 1:
        raise ValueError('id not uniquely present in official catalog')
    if type(page) is not int or page < 1:
        raise ValueError('page must be positive')
    item = matches[0]
    raw = _get(item['url'], 15000000)
    if not raw.startswith(b'%PDF-'):
        raise ValueError('expected PDF')
    with fitz.open(stream=raw, filetype='pdf') as doc:
        if page > len(doc):
            raise ValueError('page exceeds document length')
        content = doc[page - 1].get_text()
        if not content.strip():
            raise ValueError('page has no extractable text')
        return {'source': '中国人民银行区域金融运行报告', 'edition': year, 'title': item['title'], 'source_url': item['url'], 'sha256': hashlib.sha256(raw).hexdigest(), 'page': page, 'total_pages': len(doc), 'text': content, 'note': 'PDF原生文本按页返回；表格提取顺序不一定等于视觉列顺序，数值需查看原PDF，不作自动结构化或OCR。报告年份与统计年份不同，请核对。'}
