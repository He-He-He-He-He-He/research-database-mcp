"""Search FAO/IFAD/UNICEF/WFP/WHO SOFI 2024 report PDF, preserving page text."""
import release_runtime
import argparse
import io
import json
import requests
from pypdf import PdfReader
URL = 'https://docs.wfp.org/api/documents/WFP-0000160501/download/'
DOCUMENT = 'https://www.who.int/publications/m/item/the-state-of-food-security-and-nutrition-in-the-world-2024'
MAX_BYTES = 15000000

def _reader():
    with requests.get(URL, timeout=40, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for block in r.iter_content(65536):
            raw.extend(block)
            if len(raw) > MAX_BYTES:
                raise ValueError('report exceeds size limit')
    reader = PdfReader(io.BytesIO(raw))
    if len(reader.pages) != 286:
        raise ValueError('unexpected page count; check report version')
    return reader

def search(keyword, start_page=1, end_page=286, limit=20):
    if not isinstance(keyword, str) or not 2 <= len(keyword.strip()) <= 100:
        raise ValueError('invalid keyword')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start_page, end_page, limit))) or not 1 <= start_page <= end_page <= 286 or (not 1 <= limit <= 100):
        raise ValueError('invalid page range or limit')
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
    return {'source': URL, 'publication': DOCUMENT, 'published': '2024-07-24', 'title': 'The State of Food Security and Nutrition in the World 2024', 'page_range': [start_page, end_page], 'total_matches': total, 'returned': len(results), 'results': results, 'note': 'Page numbers are one-based PDF pages, not printed numbers. Extracted tables may lose column alignment or footnotes; inspect original PDF and headers before interpreting values. Estimates, survey periods and units differ.'}

def page(number):
    if isinstance(number, bool) or not isinstance(number, int) or (not 1 <= number <= 286):
        raise ValueError('invalid PDF page')
    r = _reader()
    return {'source': URL, 'published': '2024-07-24', 'pdf_page': number, 'text': r.pages[number - 1].extract_text(), 'note': 'Raw PDF page text; figures, table alignment, superscripts and footnotes may be lost. Check original PDF before use.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='command', required=True)
    q = s.add_parser('search')
    q.add_argument('keyword')
    q.add_argument('--start-page', type=int, default=1)
    q.add_argument('--end-page', type=int, default=286)
    q.add_argument('--limit', type=int, default=20)
    q = s.add_parser('page')
    q.add_argument('page', type=int)
    a = p.parse_args()
    out = search(a.keyword, a.start_page, a.end_page, a.limit) if a.command == 'search' else page(a.page)
    print(json.dumps(out, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
