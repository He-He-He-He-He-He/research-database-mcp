"""China National Intellectual Property Administration patent survey reports."""
import release_runtime
import io
import requests
from pypdf import PdfReader
URLS = {2023: 'https://www.cnipa.gov.cn/module/download/downfile.jsp?classid=0&showname=2023%E5%B9%B4%E4%B8%AD%E5%9B%BD%E4%B8%93%E5%88%A9%E8%B0%83%E6%9F%A5%E6%8A%A5%E5%91%8A.pdf&filename=bf5fc071a77b49d6ac79291cc861b047.pdf', 2024: 'https://www.cnipa.gov.cn/attach/0/aaf2cdea693842ff8dd65d78f7d0f8b3.pdf', 2025: 'https://www.cnipa.gov.cn/module/download/down.jsp?colID=88&i_ID=205590'}

def report(year, keyword=''):
    if year not in URLS:
        raise ValueError('available survey years: 2023, 2024, 2025')
    if not isinstance(keyword, str):
        raise ValueError('keyword must be a string')
    r = requests.get(URLS[year], timeout=60)
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
    return {'survey_year': year, 'source': '国家知识产权局', 'source_url': URLS[year], 'total_pdf_pages': len(pdf.pages), 'pages_with_extractable_text': text_pages, 'pages': pages}
