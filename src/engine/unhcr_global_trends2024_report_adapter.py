"""UNHCR Global Trends 2024, original report published June 2025."""
import release_runtime
import argparse
import io
import json
import requests
from pypdf import PdfReader
URL = 'https://www.unhcr.org/sites/default/files/2025-06/global-trends-report-2024.pdf'
PUBLICATION = 'https://www.unhcr.org/publications/global-trends-2024'
PORTAL = 'https://data.unhcr.org/en/documents/details/117061'
MAX_BYTES = 10000000

def _reader():
    with requests.get(URL, timeout=40, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for block in r.iter_content(65536):
            raw.extend(block)
            if len(raw) > MAX_BYTES:
                raise ValueError('PDF exceeds size limit')
    reader = PdfReader(io.BytesIO(raw))
    if len(reader.pages) != 64:
        raise ValueError('unexpected page count; check report version')
    return reader

def search(keyword, start_page=1, end_page=64, limit=20):
    if not isinstance(keyword, str) or not 2 <= len(keyword.strip()) <= 100:
        raise ValueError('invalid keyword')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start_page, end_page, limit))) or not 1 <= start_page <= end_page <= 64 or (not 1 <= limit <= 100):
        raise ValueError('invalid range or limit')
    reader = _reader()
    results = []
    total = 0
    for n in range(start_page, end_page + 1):
        lines = reader.pages[n - 1].extract_text().splitlines()
        for j, line in enumerate(lines):
            if keyword.casefold() not in line.casefold():
                continue
            total += 1
            if len(results) < limit:
                results.append({'pdf_page': n, 'line': j + 1, 'text': line, 'previous_line': lines[j - 1] if j else None, 'next_line': lines[j + 1] if j + 1 < len(lines) else None})
    return {'source': URL, 'publication': PUBLICATION, 'report_page_date': '2025-06-12', 'portal': PORTAL, 'portal_published': '2025-06-16', 'portal_uploaded': '2025-06-20', 'page_range': [start_page, end_page], 'total_matches': total, 'returned': len(results), 'results': results, 'note': 'One-based PDF pages, not printed page numbers. Extraction can split sentences, headings or tables. Read original page and notes. Displacement stock, refugees, asylum seekers, returns and stateless populations have different definitions and may overlap.'}

def page(number):
    if isinstance(number, bool) or not isinstance(number, int) or (not 1 <= number <= 64):
        raise ValueError('invalid PDF page')
    return {'source': URL, 'publication': PUBLICATION, 'report_page_date': '2025-06-12', 'pdf_page': number, 'text': _reader().pages[number - 1].extract_text(), 'note': 'Raw text; layout, charts, superscripts, footnotes and table alignment may be lost. Check PDF.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='command', required=True)
    q = s.add_parser('search')
    q.add_argument('keyword')
    q.add_argument('--start-page', type=int, default=1)
    q.add_argument('--end-page', type=int, default=64)
    q.add_argument('--limit', type=int, default=20)
    q = s.add_parser('page')
    q.add_argument('page', type=int)
    a = p.parse_args()
    out = search(a.keyword, a.start_page, a.end_page, a.limit) if a.command == 'search' else page(a.page)
    print(json.dumps(out, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
