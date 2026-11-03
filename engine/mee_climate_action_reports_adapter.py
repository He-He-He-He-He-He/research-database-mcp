"""生态环境部应对气候变化政策与行动年度报告 PDF 正文检索。"""
import release_runtime
import hashlib
import requests, fitz
SOURCES = {2023: 'https://www.mee.gov.cn/ywgz/ydqhbh/wsqtkz/202310/W020231027674250657087.pdf', 2024: 'https://www.mee.gov.cn/ywgz/ydqhbh/wsqtkz/202411/W020241106685054014098.pdf', 2025: 'https://www.mee.gov.cn/ywgz/ydqhbh/wsqtkz/202510/W020251029517340644930.pdf', 2026: 'https://www.mee.gov.cn/ywgz/ydqhbh/qhbhlf/202610/W020261021337934232125.pdf'}

def catalog():
    return {'source': '生态环境部中国应对气候变化的政策与行动年度报告', 'items': [{'year': y, 'title': f'中国应对气候变化的政策与行动{y}年度报告', 'pdf_url': url} for y, url in sorted(SOURCES.items(), reverse=True)], 'note': '固定官方报告文件，非完整历史目录；报告年份不等于所有指标的数据年份。'}

def search(year, keyword, limit=10):
    if isinstance(year, bool) or not isinstance(year, int) or year not in SOURCES:
        raise ValueError('year 须为 2023–2026')
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('关键词须为 1–100 字')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50):
        raise ValueError('limit 须为 1–50')
    with requests.get(SOURCES[year], timeout=(10, 35), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('来源重定向')
        raw = bytearray()
        for chunk in r.iter_content(65536):
            raw.extend(chunk)
            if len(raw) > 30000000:
                raise ValueError('文件超过上限')
    if not raw.startswith(b'%PDF-'):
        raise ValueError('非 PDF')
    doc = fitz.open(stream=bytes(raw), filetype='pdf')
    if len(doc) > 500:
        raise ValueError('页数超出上限')
    hits = []
    total = 0
    for p in doc:
        text = p.get_text()
        if keyword in text:
            total += 1
            if len(hits) < limit:
                hits.append({'page': p.number + 1, 'text': text})
    return {'source': '生态环境部中国应对气候变化的政策与行动年度报告', 'year': year, 'pdf_url': SOURCES[year], 'sha256': hashlib.sha256(raw).hexdigest(), 'pdf_pages': len(doc), 'keyword': keyword, 'matched_pages': total, 'hits': hits, 'note': '报告涵盖不同政策和数据年份；按 PDF 物理页检索可提取文字，图表、图片、扫描页未 OCR，页码与印刷页可能不同，数据口径及背景请核原文。'}
