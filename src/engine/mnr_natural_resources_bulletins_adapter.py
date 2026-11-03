"""中国自然资源公报 2023、2024 官方 PDF 全文页检索。"""
import release_runtime
import hashlib
import requests, fitz
SOURCES = {2023: 'https://m.mnr.gov.cn/gk/tzgg/202402/P020240229684355601875.pdf', 2024: 'https://www.gov.cn/lianbo/bumen/202503/P020250322461627579892.pdf'}

def catalog():
    return {'source': '自然资源部中国自然资源公报', 'items': [{'year': y, 'title': f'{y}年中国自然资源公报', 'pdf_url': u} for y, u in sorted(SOURCES.items(), reverse=True)], 'note': '固定已验证文件，不是完整公报目录；2024 文件由中国政府网发布。公报部分数据隔年发布，年份以对应统计说明为准。'}

def search(year, keyword, limit=10):
    if isinstance(year, bool) or not isinstance(year, int) or year not in SOURCES:
        raise ValueError('支持 2023、2024 年')
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('关键词须为 1–100 字')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50):
        raise ValueError('limit 须为 1–50')
    url = SOURCES[year]
    with requests.get(url, timeout=(15, 60), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('来源重定向')
        raw = bytearray()
        for chunk in r.iter_content(65536):
            raw.extend(chunk)
            if len(raw) > 25000000:
                raise ValueError('文件超过大小上限')
    if not raw.startswith(b'%PDF-'):
        raise ValueError('来源不是 PDF')
    d = fitz.open(stream=bytes(raw), filetype='pdf')
    if len(d) > 200:
        raise ValueError('PDF 页数超限')
    hits = []
    count = 0
    for p in d:
        text = p.get_text()
        if keyword in text:
            count += 1
            if len(hits) < limit:
                hits.append({'page': p.number + 1, 'text': text})
    return {'source': '自然资源部中国自然资源公报', 'year': year, 'pdf_url': url, 'pdf_sha256': hashlib.sha256(raw).hexdigest(), 'pdf_pages': len(d), 'keyword': keyword, 'matched_pages': count, 'hits': hits, 'note': '返回 PDF 物理页，不是统计表结构化数据。仅检索可提取文字，图表或扫描内容未 OCR；自然资源存量等部分数据隔年发布，年份、单位、统计范围及图注请核原文件。'}
