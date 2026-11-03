"""Read China Meteorological Administration annual ecological bulletins."""
import release_runtime
import io
import requests
from pypdf import PdfReader
URLS = {2024: 'https://image.nmc.cn/userfiles/ueditor/userid/files/cms/article/2025/07/1753260426079.pdf?v=1753260427359', 2025: 'https://image.nmc.cn/userfiles/ueditor/userid/files/cms/article/2026/06/1780396545149.pdf?v=1780396545557'}

def report(year, keyword=''):
    if year not in URLS:
        raise ValueError('available years: 2024, 2025')
    if not isinstance(keyword, str):
        raise ValueError('keyword must be a string')
    r = requests.get(URLS[year], timeout=90)
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
    return {'year': year, 'author': '中国气象局', 'source_url': URLS[year], 'total_pdf_pages': len(pdf.pages), 'pages_with_extractable_text': text_pages, 'pages': pages}
