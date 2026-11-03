"""WHO Noncommunicable Diseases Country Profiles 2018, PDF page text search."""
import release_runtime
import io, requests, fitz
URL = 'https://www.who.int/docs/default-source/ncds/9789241514620-eng.pdf'
LANDING = 'https://www.who.int/publications/i/item/9789241514620'

def search(keyword, limit=10):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('请输入 1 至 100 字符关键词')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50):
        raise ValueError('结果上限应为 1 至 50')
    with requests.get(URL, timeout=50, stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        data = bytearray()
        for b in r.iter_content(65536):
            data.extend(b)
            if len(data) > 15000000:
                raise ValueError('PDF 超过大小限制')
        modified = r.headers.get('Last-Modified')
    doc = fitz.open(stream=bytes(data), filetype='pdf')
    try:
        found = []
        total = 0
        for n, page in enumerate(doc):
            text = page.get_text()
            if keyword.casefold() in text.casefold():
                total += 1
                if len(found) < limit:
                    found.append({'pdf_page': n + 1, 'text': text})
        return {'source_pdf': URL, 'publication_page': LANDING, 'report_year': 2018, 'server_last_modified': modified, 'pdf_metadata': doc.metadata, 'page_count': len(doc), 'keyword': keyword, 'matched_pages': total, 'returned_pages': found, 'caution': 'PDF 物理页码；报告为 2018 年版，但服务器及 PDF 元数据时间可能更晚，不证明文件与首版一致。不同指标年份及估计方法须参照报告；文字提取不保证图形、颜色或表格的完整和顺序，请核对原页。上限只影响返回页数，匹配页数不等于国家数。'}
    finally:
        doc.close()
