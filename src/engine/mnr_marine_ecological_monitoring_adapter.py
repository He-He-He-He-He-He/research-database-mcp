"""Natural Resources Ministry marine ecological monitoring bulletins (PDF)."""
import release_runtime
import io
import requests
from pypdf import PdfReader
REPORTS = {2023: ('https://www.gov.cn/lianbo/bumen/202406/P020240613437680507415.pdf', '中国政府网'), 2024: ('https://gi.mnr.gov.cn/202506/P020250611636525426600.pdf', '自然资源部')}

def report(year, keyword=''):
    if year not in REPORTS:
        raise ValueError('available years: 2023, 2024')
    if not isinstance(keyword, str):
        raise ValueError('keyword must be a string')
    url, host = REPORTS[year]
    chunks, size = ([], 0)
    with requests.get(url, timeout=120, stream=True) as response:
        response.raise_for_status()
        for chunk in response.iter_content(1024 * 1024):
            size += len(chunk)
            if size > 128 * 1024 * 1024:
                raise ValueError('PDF 超过 128 MiB 上限')
            chunks.append(chunk)
    content = b''.join(chunks)
    if not content.startswith(b'%PDF-'):
        raise ValueError('response is not a PDF')
    pdf = PdfReader(io.BytesIO(content))
    pages = []
    text_pages = 0
    for n, page in enumerate(pdf.pages, 1):
        text = page.extract_text() or ''
        if text.strip():
            text_pages += 1
        if keyword.casefold() in text.casefold():
            pages.append({'pdf_page': n, 'text': text})
    return {'year': year, 'author': '自然资源部', 'hosting_source': host, 'source_url': url, 'total_pdf_pages': len(pdf.pages), 'pages_with_extractable_text': text_pages, 'pages': pages}
