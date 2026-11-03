"""Official Hainan 2024 statistical yearbook PDF."""
import release_runtime
import io
import unicodedata
import requests
from pypdf import PdfReader
URL = 'https://stats.hainan.gov.cn/tjj/tjsu/ndsj/2024/202412/P020250116308974141111.pdf'
SOURCE = '海南省统计局《海南统计年鉴2024》'

def document():
    r = requests.get(URL, timeout=120)
    r.raise_for_status()
    if not r.content.startswith(b'%PDF-'):
        raise ValueError('response is not a PDF')
    return {'source': SOURCE, 'edition': 2024, 'url': URL, 'content_type': 'application/pdf', 'content': r.content}

def page(number):
    if isinstance(number, bool) or not isinstance(number, int) or number < 1:
        raise ValueError('page must be a positive 1-based PDF page number')
    d = document()
    pdf = PdfReader(io.BytesIO(d.pop('content')))
    if number > len(pdf.pages):
        raise ValueError('page outside PDF')
    return {**d, 'pdf_page': number, 'page_count': len(pdf.pages), 'text': pdf.pages[number - 1].extract_text() or ''}

def search(keyword, limit=20):
    if not isinstance(keyword, str) or not keyword.strip():
        raise ValueError('keyword required')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('limit must be between 1 and 100')
    d = document()
    pdf = PdfReader(io.BytesIO(d.pop('content')))
    results = []
    needle = ''.join(unicodedata.normalize('NFKC', keyword).split())
    for i, p in enumerate(pdf.pages, 1):
        txt = p.extract_text() or ''
        if needle in ''.join(unicodedata.normalize('NFKC', txt).split()):
            results.append({**d, 'pdf_page': i, 'text': txt})
            if len(results) == limit:
                break
    return results
