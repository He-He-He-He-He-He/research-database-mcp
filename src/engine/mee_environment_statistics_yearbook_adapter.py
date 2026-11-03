"""生态环境部全国生态环境统计年报官方 PDF 页内检索。"""
import release_runtime
import hashlib, re
from urllib.parse import urljoin, urlsplit
import requests, fitz
from bs4 import BeautifulSoup
INDEX = 'https://www.mee.gov.cn/hjzl/sthjzk/sthjtjnb/'

def _get(url, cap=40000000):
    with requests.get(url, timeout=35, allow_redirects=False, stream=True) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('上游重定向')
        out = bytearray()
        for part in r.iter_content(65536):
            out.extend(part)
            if len(out) > cap:
                raise ValueError('来源文件超过大小上限')
        return bytes(out)

def catalog():
    s = BeautifulSoup(_get(INDEX), 'html.parser')
    out = {}
    for a in s.select('a[href]'):
        title = a.get_text(' ', strip=True)
        m = re.fullmatch('(20\\d{2})年中国生态环境统计年报', title)
        if not m:
            continue
        url = urljoin(INDEX, a['href'])
        p = urlsplit(url)
        if p.scheme == 'https' and p.hostname == 'www.mee.gov.cn' and re.fullmatch('/hjzl/sthjzk/sthjtjnb/\\d{6}/t\\d{8}_\\d+\\.shtml', p.path):
            out.setdefault(m.group(1), {'year': int(m.group(1)), 'title': title, 'url': url})
    if not out:
        raise ValueError('未识别官方年报目录')
    return {'source': '生态环境部中国生态环境统计年报', 'source_url': INDEX, 'items': sorted(out.values(), key=lambda x: x['year'], reverse=True), 'note': '官方目录；各年数据范围、统计调查制度和最终修订口径可能不同。'}

def search(year, keyword):
    if isinstance(year, bool) or not isinstance(year, int):
        raise ValueError('年份必须为整数')
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('关键词须为1–100字')
    item = next((x for x in catalog()['items'] if x['year'] == year), None)
    if not item:
        raise ValueError('年报未在目录中')
    s = BeautifulSoup(_get(item['url']), 'html.parser')
    urls = []
    for a in s.select('a[href]'):
        u = urljoin(item['url'], a['href'])
        p = urlsplit(u)
        if p.scheme == 'https' and p.hostname == 'www.mee.gov.cn' and re.fullmatch('/hjzl/sthjzk/sthjtjnb/\\d{6}/[A-Za-z0-9_-]+\\.pdf', p.path, re.I) and (u not in urls):
            urls.append(u)
    if len(urls) != 1:
        raise ValueError('未识别唯一官方年报 PDF')
    raw = _get(urls[0])
    if not raw.startswith(b'%PDF-'):
        raise ValueError('来源不是 PDF')
    doc = fitz.open(stream=raw, filetype='pdf')
    if len(doc) > 500:
        raise ValueError('PDF 页数超出上限')
    hits = []
    for p in doc:
        text = p.get_text()
        if keyword in text:
            hits.append({'page': p.number + 1, 'text': text})
    return {'source': '生态环境部中国生态环境统计年报', 'year': year, 'catalog_url': item['url'], 'pdf_url': urls[0], 'sha256': hashlib.sha256(raw).hexdigest(), 'pdf_pages': len(doc), 'keyword': keyword, 'hits': hits, 'note': 'PDF 物理页码与印刷页码可能不同；仅搜索可提取文字，图表、图片和扫描页未 OCR。污染物排放、去除和处理量不同，数据范围、单位、附注及修订应核对 PDF。'}
