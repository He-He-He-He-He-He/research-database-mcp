"""国家林草局林业和草原统计年鉴：官方目录及 PDF 原始单页提取。"""
import release_runtime
import hashlib, re
from urllib.parse import urljoin, urlsplit
import requests, fitz
from bs4 import BeautifulSoup
INDEX = 'https://www.forestry.gov.cn/c/www/tjnj.jhtml'

def _get(url, cap=80000000):
    with requests.get(url, timeout=(15, 90), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('官方来源发生重定向')
        buf = bytearray()
        for chunk in r.iter_content(65536):
            buf.extend(chunk)
            if len(buf) > cap:
                raise ValueError('文件超过 80 MB 上限')
        return bytes(buf)

def catalog():
    soup = BeautifulSoup(_get(INDEX, 2000000), 'html.parser')
    items = []
    for a in soup.select('a[href]'):
        title = a.get_text(' ', strip=True)
        m = re.fullmatch('中国林业和草原统计年鉴(20\\d{2})', title)
        url = urljoin(INDEX, a['href'])
        p = urlsplit(url)
        if m and p.scheme == 'https' and (p.hostname == 'www.forestry.gov.cn') and p.path.lower().endswith('.pdf') and (p.path.startswith('/u/cms/www/') or p.path.startswith('/html/main/')):
            items.append({'year': int(m[1]), 'title': title, 'pdf_url': url})
    if not items:
        raise ValueError('未识别官方年鉴目录')
    return {'source': '国家林业和草原局中国林业和草原统计年鉴', 'source_url': INDEX, 'items': items, 'note': '年份是年鉴标记，具体统计数据年份、指标范围及单位需核原表。'}

def page(year, page_number):
    if isinstance(year, bool) or not isinstance(year, int):
        raise ValueError('年份须为整数')
    if isinstance(page_number, bool) or not isinstance(page_number, int) or page_number < 1:
        raise ValueError('page_number 须为正整数')
    item = next((x for x in catalog()['items'] if x['year'] == year), None)
    if not item:
        raise ValueError('该年份不在当前目录中')
    raw = _get(item['pdf_url'])
    if not raw.startswith(b'%PDF-'):
        raise ValueError('下载文件非 PDF')
    doc = fitz.open(stream=raw, filetype='pdf')
    if len(doc) > 1000 or page_number > len(doc):
        raise ValueError('PDF 页数超限或所选页不存在')
    out = fitz.open()
    out.insert_pdf(doc, from_page=page_number - 1, to_page=page_number - 1)
    data = out.tobytes(garbage=3, deflate=True)
    return {'source': '国家林业和草原局中国林业和草原统计年鉴', **item, 'source_sha256': hashlib.sha256(raw).hexdigest(), 'source_bytes': len(raw), 'pdf_pages': len(doc), 'physical_page': page_number, 'page_pdf_bytes': data, 'extracted_text': doc[page_number - 1].get_text(), 'note': 'pdf_pages 与 physical_page 均为 PDF 物理页数，可能不同于印刷页码；返回的单页 PDF 保持原始页面，扫描图通常无可提取文字，未 OCR、未自动解析表格。请核原表表头、脚注和统计范围。'}
