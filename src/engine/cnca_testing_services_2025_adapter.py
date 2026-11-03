"""2025 national inspection and testing services bulletin from CNCA QTS."""
import release_runtime
import io
import requests
from pypdf import PdfReader
URL = 'https://qts.cnca.cn/qts/common/downloadFiles?fileId=d4f6cbc7a89b4ab2b0d75804cf749a3b'

def report(keyword=''):
    if not isinstance(keyword, str):
        raise ValueError('keyword must be a string')
    r = requests.get(URL, timeout=40)
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
    return {'year': 2025, 'source': '国家市场监督管理总局', 'hosting_source': '国家认监委检验检测统计直报系统', 'source_url': URL, 'total_pdf_pages': len(pdf.pages), 'pages_with_extractable_text': text_pages, 'pages': pages}
