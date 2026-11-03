"""国务院关税税则委员会 2025、2026 年进出口税则原 PDF 页检索。"""
import release_runtime
import hashlib, re
import requests, fitz
REPORTS = {2025: 'https://m.mof.gov.cn/czxw/202412/P020250127378158317243.pdf', 2026: 'https://gss.mof.gov.cn/gzdt/zhengcefabu/202512/P020251231607833453633.pdf'}

def catalog():
    return {'source': '国务院关税税则委员会', 'items': [{'year': y, 'pdf_url': u} for y, u in REPORTS.items()], 'note': '两份正式发布的年度税则原文；后续公告、原产地和税种等可能影响实际适用。'}

def search(year, keyword, limit=10):
    if isinstance(year, bool) or not isinstance(year, int) or year not in REPORTS:
        raise ValueError('仅支持2025、2026年正式税则')
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('关键词须为1–100字')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 30):
        raise ValueError('返回页数限制为1–30')
    u = REPORTS[year]
    out = bytearray()
    with requests.get(u, timeout=60, allow_redirects=False, stream=True) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('上游返回跳转')
        for part in r.iter_content(262144):
            out.extend(part)
            if len(out) > 100000000:
                raise ValueError('PDF 超过100MB')
    if not out.startswith(b'%PDF-'):
        raise ValueError('响应不是 PDF')
    raw = bytes(out)
    d = fitz.open(stream=raw, filetype='pdf')
    if len(d) > 2000:
        raise ValueError('PDF 页数超过限制')
    q = keyword.strip()
    code = re.fullmatch('\\d{8}', q)
    found = []
    total = 0
    for p in d:
        text = p.get_text()
        matched = q.casefold() in text.casefold()
        if code and (not matched):
            matched = q[:4] + '.' + q[4:] in text
        if matched:
            total += 1
            if len(found) < limit:
                found.append({'page': p.number + 1, 'text': text})
    return {'source': '国务院关税税则委员会进出口税则', 'year': year, 'source_url': u, 'sha256': hashlib.sha256(raw).hexdigest(), 'pdf_pages': len(d), 'keyword': q, 'matching_pages': total, 'items': found, 'note': '仅定位年度原表 PDF 物理页，不计算适用税率。自动提取可能打乱多栏顺序，须回看 PDF 表格；后续调整、税则号列、原产地、协定和通关条件须另核。'}
