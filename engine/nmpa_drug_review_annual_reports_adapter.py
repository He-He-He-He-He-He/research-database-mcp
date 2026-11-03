"""CDE drug review annual reports: official PDF and attributed press mirror."""
import release_runtime
import io
import requests
from pypdf import PdfReader
REPORTS = {2023: {'url': 'https://www.nmpa.gov.cn/directory/web/nmpa/images/1707039824076019627.pdf', 'host': '国家药监局官方网站'}, 2024: {'url': 'https://www.cnpharm.com/upload/resources/file/2025/03/18/170990.pdf', 'host': '中国医药报网站转载'}}

def report(year, keyword=''):
    """Extract original PDF pages, optionally retaining pages containing keyword."""
    if year not in REPORTS:
        raise ValueError('available years: 2023, 2024')
    if not isinstance(keyword, str):
        raise ValueError('keyword must be a string')
    source = REPORTS[year]
    response = requests.get(source['url'], timeout=45)
    response.raise_for_status()
    if not response.content.startswith(b'%PDF-'):
        raise ValueError('response is not a PDF')
    pdf = PdfReader(io.BytesIO(response.content))
    pages = []
    for index, page in enumerate(pdf.pages, 1):
        text = page.extract_text() or ''
        if keyword.casefold() in text.casefold():
            pages.append({'pdf_page': index, 'text': text})
    return {'year': year, 'author': '国家药品监督管理局药品审评中心', 'source_url': source['url'], 'hosting_source': source['host'], 'total_pdf_pages': len(pdf.pages), 'pages': pages}
