"""ITU Measuring Digital Development Facts and Figures 2023 PDF search."""
import release_runtime
import argparse, hashlib, io, json
import requests
from pypdf import PdfReader
URL = 'https://www.itu.int/itu-d/reports/statistics/wp-content/uploads/sites/5/2023/11/Measuring-digital-development-Facts-and-figures-2023-E.pdf'
PAGE = 'https://www.itu.int/pub/D-IND-ICT_MDD-2023-1'

def query(keyword='', start_page=1, end_page=38, limit=20):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    if any((type(x) is not int for x in (start_page, end_page, limit))) or not 1 <= start_page <= end_page <= 38 or (not 1 <= limit <= 100):
        raise ValueError('invalid page range or limit')
    with requests.get(URL, stream=True, timeout=35) as r:
        r.raise_for_status()
        modified = r.headers.get('Last-Modified')
        raw = r.raw.read(5000001, decode_content=True)
    if len(raw) > 5000000:
        raise ValueError('PDF exceeds size limit')
    reader = PdfReader(io.BytesIO(raw))
    if len(reader.pages) != 38:
        raise ValueError('unexpected page count')
    hits = []
    empty = []
    for i in range(start_page - 1, end_page):
        text = reader.pages[i].extract_text() or ''
        lines = text.splitlines()
        if not lines:
            empty.append(i + 1)
        if not keyword:
            hits.append({'pdf_page': i + 1, 'text': text})
        else:
            for n, line in enumerate(lines):
                if keyword.casefold() in line.casefold():
                    hits.append({'pdf_page': i + 1, 'line': line, 'previous_line': lines[n - 1] if n else None, 'next_line': lines[n + 1] if n + 1 < len(lines) else None})
    return {'source': URL, 'report_page': PAGE, 'edition': '2023', 'pdf_creation_date_raw': str(reader.metadata.get('/CreationDate', '')), 'pdf_modification_date_raw': str(reader.metadata.get('/ModDate', '')), 'http_last_modified': modified, 'source_sha256': hashlib.sha256(raw).hexdigest(), 'matches_in_page_range': len(hits), 'empty_text_pages': empty, 'results': hits[:limit], 'note': 'ITU estimates include current-year figures; historical values may be revised with member-state data. Verify units, denominators, dates and original footnotes; do not treat estimates as observed counts. Extracted text may omit figures or mix columns. PDF metadata and HTTP Last-Modified are not independent proof of immutable historical archive; check source usage conditions.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--keyword', default='')
    p.add_argument('--start-page', type=int, default=1)
    p.add_argument('--end-page', type=int, default=38)
    p.add_argument('--limit', type=int, default=20)
    a = p.parse_args()
    print(json.dumps(query(a.keyword, a.start_page, a.end_page, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
