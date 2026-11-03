"""MEE national noise pollution prevention reports, PDF page text."""
import release_runtime
import io
import requests
from pypdf import PdfReader
BASE = 'https://www.mee.gov.cn/hjzl/sthjzk/hjzywr/'
PATHS = {2023: '202307/W020230728374728553582.pdf', 2024: '202408/W020240829356736814731.pdf', 2025: '202511/W020251105324746322813.pdf', 2026: '202605/W020260529676177508758.pdf'}

def report(year, keyword=''):
    if year not in PATHS:
        raise ValueError('available report editions: 2023–2026')
    if not isinstance(keyword, str):
        raise ValueError('keyword must be a string')
    url = BASE + PATHS[year]
    r = requests.get(url, timeout=90)
    r.raise_for_status()
    if not r.content.startswith(b'%PDF-'):
        raise ValueError('response is not a PDF')
    pdf = PdfReader(io.BytesIO(r.content))
    pages = []
    text_pages = 0
    for number, page in enumerate(pdf.pages, 1):
        text = page.extract_text() or ''
        if text.strip():
            text_pages += 1
        if keyword.casefold() in text.casefold():
            pages.append({'pdf_page': number, 'text': text})
    return {'report_edition': year, 'source': '生态环境部', 'source_url': url, 'total_pdf_pages': len(pdf.pages), 'pages_with_extractable_text': text_pages, 'pages': pages}
