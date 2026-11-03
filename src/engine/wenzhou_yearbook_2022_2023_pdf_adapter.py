"""Official Wenzhou Statistical Yearbooks: 2022 and 2023 editions."""
import release_runtime
import io
import unicodedata
import requests
from pypdf import PdfReader
FILES = {2022: '8a3d3910be6346e0930736bbd2d2b197.pdf', 2023: '51296d6ca0bb453fbbb1e40d8d222543.pdf'}
BASE = 'https://wztjj.wenzhou.gov.cn/attach/0/'

def document(year):
    if isinstance(year, bool) or not isinstance(year, int) or year not in FILES:
        raise ValueError('available editions: 2022 and 2023')
    url = BASE + FILES[year]
    r = requests.get(url, timeout=90)
    r.raise_for_status()
    if not r.content.startswith(b'%PDF-'):
        raise ValueError('response is not a PDF')
    return {'source': f'温州市统计局《温州统计年鉴{year}》', 'edition': year, 'url': url, 'content_type': 'application/pdf', 'content': r.content}

def page(year, number):
    if isinstance(number, bool) or not isinstance(number, int) or number < 1:
        raise ValueError('page must be a positive 1-based PDF page number')
    d = document(year)
    pdf = PdfReader(io.BytesIO(d.pop('content')))
    if number > len(pdf.pages):
        raise ValueError('page outside PDF')
    return {**d, 'pdf_page': number, 'page_count': len(pdf.pages), 'text': pdf.pages[number - 1].extract_text() or ''}

def search(year, keyword, limit=20):
    if not isinstance(keyword, str) or not keyword.strip():
        raise ValueError('keyword required')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('limit must be between 1 and 100')
    d = document(year)
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
