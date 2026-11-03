"""Niue Statistics Office GDP 2025 report page-level extraction."""
import release_runtime
import io, hashlib
import requests
from pypdf import PdfReader
URL = 'https://niuestatistics.nu/download/32/national-accounts/3279/gdp-2025'
PAGE = 'https://niuestatistics.nu/stats/'

def report(page=1):
    if type(page) is not int or not 1 <= page <= 50:
        raise ValueError('Invalid page')
    with requests.get(URL, timeout=30, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for part in r.iter_content(65536):
            raw.extend(part)
            if len(raw) > 4000000:
                raise ValueError('PDF too large')
        modified = r.headers.get('Last-Modified')
    if not raw.startswith(b'%PDF-'):
        raise ValueError('Upstream did not return a PDF')
    p = PdfReader(io.BytesIO(raw))
    count = len(p.pages)
    if page > count:
        raise ValueError('Page exceeds report length')
    return {'source': URL, 'source_page': PAGE, 'sha256': hashlib.sha256(raw).hexdigest(), 'last_modified_header': modified, 'pdf_pages': count, 'page': page, 'text': p.pages[page - 1].extract_text(extraction_mode='layout'), 'notes': ['Official Niue Statistics Office national accounts estimates for year ending June 2025; report marks 2025 P and discusses it as projected.', 'Base year 2019; GDP amounts are NZD thousands and per-capita values are NZD. Check the exact table headers and source.', 'PDF text extraction may reorder columns, omit visual charts or alter table layout; inspect the original page for numeric citations.', 'This 2026 release cannot establish what was available at an earlier historical cutoff.']}
