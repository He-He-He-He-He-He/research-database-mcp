"""Read official Huaihua Statistical Yearbook 2024 PDF."""
import release_runtime
import io
import unicodedata
import requests
from pypdf import PdfReader
URL = 'https://www.huaihua.gov.cn/tjj/c134105/202506/4933ceeea5db485b94e3222e41fd6854/files/1b4742cbe0344d29ab541278692c23bb.pdf'
SOURCE = '怀化市统计局《怀化统计年鉴2024》'

def document():
    r = requests.get(URL, timeout=90)
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
    result = []
    needle = ''.join(unicodedata.normalize('NFKC', keyword).split())
    for i, p in enumerate(pdf.pages, 1):
        txt = p.extract_text() or ''
        if needle in ''.join(unicodedata.normalize('NFKC', txt).split()):
            result.append({**d, 'pdf_page': i, 'text': txt})
            if len(result) == limit:
                break
    return result
