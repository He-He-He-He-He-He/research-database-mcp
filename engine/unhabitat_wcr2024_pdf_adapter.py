"""UN-Habitat World Cities Report 2024 PDF pages and text search."""
import release_runtime
import argparse, hashlib, io, json
import requests
from pypdf import PdfReader
URL = 'https://unhabitat.org/sites/default/files/2024/11/wcr2024_-_full_report.pdf'
PAGE = 'https://unhabitat.org/world-cities-report-2024-cities-and-climate-action'

def query(keyword='', start_page=319, end_page=350, limit=20):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    if any((type(x) is not int for x in (start_page, end_page, limit))) or not 1 <= start_page <= end_page <= 373 or end_page - start_page > 99 or (not 1 <= limit <= 100):
        raise ValueError('invalid page range or limit')
    with requests.get(URL, stream=True, timeout=90) as r:
        r.raise_for_status()
        modified = r.headers.get('Last-Modified')
        raw = r.raw.read(25000001, decode_content=True)
    if len(raw) > 25000000:
        raise ValueError('PDF exceeds size limit')
    reader = PdfReader(io.BytesIO(raw))
    if len(reader.pages) != 373:
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
    return {'source': URL, 'report_page': PAGE, 'edition': '2024', 'pdf_creation_date_raw': str(reader.metadata.get('/CreationDate', '')), 'pdf_modification_date_raw': str(reader.metadata.get('/ModDate', '')), 'http_last_modified': modified, 'source_sha256': hashlib.sha256(raw).hexdigest(), 'matches_in_page_range': len(hits), 'empty_text_pages': empty, 'results': hits[:limit], 'note': 'UN-Habitat World Cities Report 2024. Current PDF metadata indicates a June 2025 modification; this is not established as the original 2024 release, nor is server time independent historical archive proof. Tables include estimates and future projections; preserve years, geographic definitions, units and footnotes and verify on the original PDF page. PDF extraction can merge columns, lose formatting or omit graphics. Each request downloads roughly 18 MB.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--keyword', default='')
    p.add_argument('--start-page', type=int, default=319)
    p.add_argument('--end-page', type=int, default=350)
    p.add_argument('--limit', type=int, default=20)
    a = p.parse_args()
    print(json.dumps(query(a.keyword, a.start_page, a.end_page, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
