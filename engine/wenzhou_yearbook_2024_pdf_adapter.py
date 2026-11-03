"""Read and search official Wenzhou Statistical Yearbook, 2024 edition."""
import release_runtime
import io
import unicodedata
import requests
from pypdf import PdfReader
URL = 'https://wztjj.wenzhou.gov.cn/attach/0/3f6244e96547495fa01f52ecfb5e144f.pdf'
SOURCE = '温州市统计局《温州统计年鉴2024》'

def _reader():
    r = requests.get(URL, timeout=90)
    r.raise_for_status()
    if not r.content.startswith(b'%PDF-'):
        raise ValueError('response is not a PDF')
    return PdfReader(io.BytesIO(r.content))

def document():
    r = requests.get(URL, timeout=90)
    r.raise_for_status()
    if not r.content.startswith(b'%PDF-'):
        raise ValueError('response is not a PDF')
    return {'source': SOURCE, 'edition': 2024, 'url': URL, 'content_type': 'application/pdf', 'content': r.content}

def page(number):
    if isinstance(number, bool) or not isinstance(number, int) or number < 1:
        raise ValueError('page must be a positive 1-based PDF page number')
    pdf = _reader()
    if number > len(pdf.pages):
        raise ValueError('page outside PDF')
    return {'source': SOURCE, 'edition': 2024, 'url': URL, 'pdf_page': number, 'page_count': len(pdf.pages), 'text': pdf.pages[number - 1].extract_text() or ''}

def search(keyword, limit=20):
    if not isinstance(keyword, str) or not keyword.strip():
        raise ValueError('keyword required')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('limit must be between 1 and 100')
    pdf = _reader()
    result = []
    needle = ''.join(unicodedata.normalize('NFKC', keyword).split())
    for i, p in enumerate(pdf.pages, 1):
        text = p.extract_text() or ''
        if needle in ''.join(unicodedata.normalize('NFKC', text).split()):
            result.append({'source': SOURCE, 'url': URL, 'pdf_page': i, 'text': text})
            if len(result) == limit:
                break
    return result
