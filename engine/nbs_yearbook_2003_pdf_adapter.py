"""Official China Statistical Yearbook 2003 PDF page search and candidate tables."""
import release_runtime
import contextlib, io
import requests, fitz
URL = 'https://www.stats.gov.cn/sj/ndsj/yearbook2003_c.pdf'

def _open():
    with requests.get(URL, timeout=(10, 60), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        raw = bytearray()
        for part in r.iter_content(65536):
            raw.extend(part)
            if len(raw) > 15000000:
                raise ValueError('PDF exceeds limit')
    if not raw.startswith(b'%PDF-'):
        raise ValueError('invalid PDF')
    doc = fitz.open(stream=bytes(raw), filetype='pdf')
    if not 1 <= len(doc) <= 1200:
        raise ValueError('unexpected PDF length')
    return doc

def search(keyword, limit=20):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('nonempty keyword up to 100 characters required')
    if type(limit) is not int or not 1 <= limit <= 50:
        raise ValueError('limit 1–50')
    doc = _open()
    matches = []
    count = 0
    for page in doc:
        text = page.get_text()
        at = text.find(keyword)
        if at >= 0:
            count += 1
            if len(matches) < limit:
                matches.append({'physical_page': page.number + 1, 'excerpt': text[max(0, at - 100):at + len(keyword) + 180]})
    return {'yearbook_year': 2003, 'pdf_url': URL, 'total_pdf_pages': len(doc), 'keyword': keyword, 'matched_pages': count, 'items': matches, 'note': '按 PDF 可提取文本检索，可能漏掉图像或字间空格；物理页码与印刷页码可能不同。'}

def page(page_number):
    if type(page_number) is not int or page_number < 1:
        raise ValueError('page must be positive integer')
    doc = _open()
    if page_number > len(doc):
        raise ValueError('page out of range')
    p = doc[page_number - 1]
    with contextlib.redirect_stdout(io.StringIO()):
        tabs = p.find_tables().tables
    return {'yearbook_year': 2003, 'pdf_url': URL, 'total_pdf_pages': len(doc), 'physical_page': page_number, 'text': p.get_text(), 'candidate_tables': [x.extract() for x in tabs], 'note': '自动识表可能错行、错列、遗漏跨页表头；请核原页，不将空白当作零。'}
