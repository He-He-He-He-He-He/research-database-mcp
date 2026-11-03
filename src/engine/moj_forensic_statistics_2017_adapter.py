"""司法部 2017 年全国司法鉴定统计分析：PDF 页级文本检索。"""
import release_runtime
import io, re
import requests
from pypdf import PdfReader
URL = 'https://www.moj.gov.cn/pub/sfbgw/zwxxgk/fdzdgknr/fdzdgknrtjxx/201806/P020210331719199367931.pdf'

def search(keyword='', offset=0, limit=10):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('keyword 须为不超过100字的字符串')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 20):
        raise ValueError('offset 须非负且 limit 介于1至20')
    with requests.get(URL, timeout=(12, 30), stream=True, allow_redirects=True) as r:
        r.raise_for_status()
        if any((not h.url.startswith('https://www.moj.gov.cn/') for h in [*r.history, r])):
            raise RuntimeError('跳转离开司法部域名')
        chunks = []
        size = 0
        for c in r.iter_content(65536):
            size += len(c)
            if size > 8000000:
                raise RuntimeError('PDF 超过8MB限制')
            chunks.append(c)
    raw = b''.join(chunks)
    if not raw.startswith(b'%PDF-'):
        raise RuntimeError('官方响应不是PDF')
    pdf = PdfReader(io.BytesIO(raw))
    if len(pdf.pages) != 13:
        raise RuntimeError('PDF 页数与预期不符')
    rows = []
    key = re.sub('\\s+', '', keyword).casefold()
    for i, p in enumerate(pdf.pages):
        t = p.extract_text() or ''
        if not key or key in re.sub('\\s+', '', t).casefold():
            rows.append({'pdf_page': i + 1, 'text': t, 'image_count': len(p.images)})
    if not any(('2017' in (p.extract_text() or '') for p in pdf.pages[:2])):
        raise RuntimeError('未识别报告年份')
    return {'source': '中华人民共和国司法部', 'year': 2017, 'url': URL, 'keyword': keyword, 'total_pages': len(pdf.pages), 'matched_pages': len(rows), 'offset': offset, 'limit': limit, 'items': rows[offset:offset + limit], 'note': '历史报告原 PDF 页级文字；页码为 PDF 顺序，可能不同于印刷页码；检索时忽略空白但保留 PDF 原文本。图片及图表未识别，图中文字、表结构、分母口径和数字应核对原 PDF，不能代表当前状况。'}
