"""生态环境部历史全国自然保护区名录：官方目录和 PDF 文字页检索。"""
import release_runtime
import hashlib
import re
from urllib.parse import urljoin, urlsplit
import fitz
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.mee.gov.cn/ywgz/zrstbh/zrbhdjg/'

def _get(url, cap=25000000):
    with requests.get(url, timeout=40, allow_redirects=False, stream=True) as response:
        response.raise_for_status()
        if response.is_redirect:
            raise ValueError('官方来源发生重定向')
        data = bytearray()
        for chunk in response.iter_content(65536):
            data.extend(chunk)
            if len(data) > cap:
                raise ValueError('来源文件超过大小上限')
        return bytes(data)

def catalog():
    found = {}
    for suffix in ('index.shtml', 'index_1.shtml', 'index_2.shtml', 'index_3.shtml'):
        index = urljoin(BASE, suffix)
        soup = BeautifulSoup(_get(index), 'html.parser')
        for link in soup.select('a[href]'):
            title = link.get_text(' ', strip=True)
            match = re.fullmatch('(20\\d{2})年全国自然保护区名录', title)
            url = urljoin(index, link['href'])
            parts = urlsplit(url)
            if match and parts.scheme == 'https' and (parts.hostname == 'www.mee.gov.cn') and re.fullmatch('/ywgz/zrstbh/zrbhdjg/\\d{6}/P\\w+\\.pdf', parts.path, re.I):
                found[int(match.group(1))] = {'year': int(match.group(1)), 'title': title, 'pdf_url': url, 'index_url': index}
    if not found:
        raise ValueError('未识别到历史名录')
    return {'source': '生态环境部全国自然保护区历史名录', 'items': sorted(found.values(), key=lambda item: item['year'], reverse=True), 'note': '各名录为对应年份历史快照；保护地整合、名称、边界与级别可能变动，不能代表现状。'}

def search(year, keyword, limit=10):
    if isinstance(year, bool) or not isinstance(year, int):
        raise ValueError('年份必须为整数')
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('关键词须为 1–100 字')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50):
        raise ValueError('limit 须为 1–50')
    item = next((x for x in catalog()['items'] if x['year'] == year), None)
    if item is None:
        raise ValueError('年份不在官方目录中')
    raw = _get(item['pdf_url'])
    if not raw.startswith(b'%PDF-'):
        raise ValueError('来源不是 PDF')
    doc = fitz.open(stream=raw, filetype='pdf')
    if len(doc) > 500:
        raise ValueError('PDF 页数超过上限')
    hits = []
    count = 0
    for page in doc:
        text = page.get_text()
        if keyword in text:
            count += 1
            if len(hits) < limit:
                hits.append({'page': page.number + 1, 'text': text})
    return {'source': '生态环境部全国自然保护区历史名录', **item, 'sha256': hashlib.sha256(raw).hexdigest(), 'pdf_pages': len(doc), 'keyword': keyword, 'matched_pages': count, 'hits': hits, 'note': '返回匹配页而非自动结构化记录；页号为 PDF 物理页号。仅检索可提取文字，扫描图像未 OCR；表格列可能拼接，行政区域、面积、级别和脚注请对照原表。历史名录不能用于判断当前状态或法律边界。'}
