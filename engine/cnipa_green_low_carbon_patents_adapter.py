"""CNIPA green and low-carbon patent statistical analysis reports."""
import release_runtime
import io
import requests
from pypdf import PdfReader
URLS = {2024: 'https://www.cnipa.gov.cn/module/download/downfile.jsp?classid=0&showname=%E7%BB%BF%E8%89%B2%E4%BD%8E%E7%A2%B3%E4%B8%93%E5%88%A9%E7%BB%9F%E8%AE%A1%E5%88%86%E6%9E%90%E6%8A%A5%E5%91%8A%EF%BC%882024%EF%BC%89.pdf&filename=bc3d1d4d85cb40f8b48df30e6102d48a.pdf', 2025: 'https://www.cnipa.gov.cn/module/download/downfile.jsp?classid=0&showname=%E9%99%84%E4%BB%B61%20%E7%BB%BF%E8%89%B2%E4%BD%8E%E7%A2%B3%E4%B8%93%E5%88%A9%E7%BB%9F%E8%AE%A1%E5%88%86%E6%9E%90%E6%8A%A5%E5%91%8A%EF%BC%882025%EF%BC%89.pdf&filename=207265adfa874660890e578ffec3aef0.pdf'}

def report(year, keyword=''):
    if year not in URLS:
        raise ValueError('available report editions: 2024, 2025')
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
    return {'report_edition': year, 'edition_status': '专家审议稿' if year == 2025 else '未标注专家审议稿', 'source': '国家知识产权局', 'source_url': URLS[year], 'total_pdf_pages': len(pdf.pages), 'pages_with_extractable_text': text_pages, 'pages': pages}
