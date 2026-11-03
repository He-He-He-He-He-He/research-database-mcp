"""NMPA 2024 annual regulatory statistics original PDF page extraction."""
import release_runtime
import io
import requests
from pypdf import PdfReader
URL = 'https://www.nmpa.gov.cn/directory/web/nmpa/images/1755850263549015691.pdf'

def report(keyword=''):
    if not isinstance(keyword, str):
        raise ValueError('keyword must be a string')
    r = requests.get(URL, timeout=40)
    r.raise_for_status()
    if not r.content.startswith(b'%PDF-'):
        raise ValueError('not a PDF')
    pdf = PdfReader(io.BytesIO(r.content))
    pages = []
    for number, p in enumerate(pdf.pages, 1):
        text = p.extract_text() or ''
        if keyword.casefold() in text.casefold():
            pages.append({'pdf_page': number, 'text': text})
    return {'year': 2024, 'source_url': URL, 'total_pdf_pages': len(pdf.pages), 'pages': pages}
