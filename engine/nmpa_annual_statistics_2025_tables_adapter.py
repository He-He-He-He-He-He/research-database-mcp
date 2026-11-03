"""NMPA 2025 regulatory statistics, official PDF pages and candidate tables."""
import release_runtime
import contextlib, io, re
from urllib.parse import urljoin, urlsplit
import requests, fitz
LANDING = 'https://www.nmpaic.org.cn/yjzxyw/202609/t20260907_430855.html'

def _get(url, limit):
    with requests.get(url, timeout=(10, 45), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        buf = bytearray()
        for part in r.iter_content(65536):
            buf.extend(part)
            if len(buf) > limit:
                raise ValueError('response exceeds limit')
        return bytes(buf)

def source():
    html = _get(LANDING, 1000000).decode('utf-8')
    titles = re.findall('var\\s+title\\s*=\\s*[\'\\"]([^\'\\"]+)[\'\\"]', html)
    hrefs = re.findall('var\\s+href\\s*=\\s*[\'\\"]([^\'\\"]+)[\'\\"]', html)
    if titles != ['药品监督管理统计年度数据（2025年）.pdf'] or len(hrefs) != 1:
        raise ValueError('source structure changed')
    u = urljoin(LANDING, hrefs[0])
    p = urlsplit(u)
    if p.scheme != 'https' or p.netloc != 'www.nmpaic.org.cn' or (not re.fullmatch('/yjzxyw/202609/P\\d+\\.pdf', p.path)) or p.query or p.fragment:
        raise ValueError('unexpected PDF path')
    return {'landing_url': LANDING, 'pdf_url': u, 'title': titles[0], 'publisher': '国家药品监督管理局综合和规划财务司、信息中心', 'year': 2025}

def page(page_number):
    if type(page_number) is not int or page_number < 1:
        raise ValueError('page must be a positive integer')
    meta = source()
    raw = _get(meta['pdf_url'], 10000000)
    if not raw.startswith(b'%PDF-'):
        raise ValueError('invalid PDF')
    doc = fitz.open(stream=raw, filetype='pdf')
    if len(doc) > 200 or page_number > len(doc):
        raise ValueError('page out of range')
    p = doc[page_number - 1]
    with contextlib.redirect_stdout(io.StringIO()):
        table_list = p.find_tables().tables
    return {**meta, 'total_pdf_pages': len(doc), 'physical_page': page_number, 'text': p.get_text(), 'candidate_tables': [t.extract() for t in table_list], 'note': 'PDF 表格自动识别可能合并、拆列或漏数；须核对原 PDF，空白不能推断为零。物理页码可能与印刷页码不同。'}
