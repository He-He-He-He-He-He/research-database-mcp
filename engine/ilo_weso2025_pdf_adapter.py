"""Search ILO World Employment and Social Outlook Trends 2025 PDF."""
import release_runtime
import argparse, hashlib, io, json
import requests
from pypdf import PdfReader
URL = 'https://www.ilo.org/sites/default/files/2025-01/WESO25_Trends_EN_WEB5.pdf'
PAGE = 'https://www.ilo.org/publications/flagship-reports/world-employment-and-social-outlook-trends-2025'

def search(keyword, start_page=1, end_page=84, limit=20):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('invalid keyword')
    if any((type(x) is not int for x in (start_page, end_page, limit))) or not 1 <= start_page <= end_page <= 84 or (not 1 <= limit <= 100):
        raise ValueError('invalid page range or limit')
    with requests.get(URL, stream=True, timeout=40) as r:
        r.raise_for_status()
        modified = r.headers.get('Last-Modified')
        raw = r.raw.read(20000001, decode_content=True)
    if len(raw) > 20000000:
        raise ValueError('PDF exceeds limit')
    reader = PdfReader(io.BytesIO(raw))
    if len(reader.pages) != 84:
        raise ValueError('unexpected page count')
    hits = []
    empty = []
    for i in range(start_page - 1, end_page):
        lines = (reader.pages[i].extract_text() or '').splitlines()
        if not lines:
            empty.append(i + 1)
        for n, line in enumerate(lines):
            if keyword.casefold() in line.casefold():
                hits.append({'pdf_page': i + 1, 'line': line, 'previous_line': lines[n - 1] if n else None, 'next_line': lines[n + 1] if n + 1 < len(lines) else None})
    return {'source': URL, 'report_page': PAGE, 'report_publication_date': '2025-01-16', 'http_last_modified': modified, 'source_sha256': hashlib.sha256(raw).hexdigest(), 'matches_in_page_range': len(hits), 'empty_text_pages': empty, 'results': hits[:limit], 'note': 'ILO historical report; estimates and forecasts differ from observations, and indicator definitions, units, geographic scope and dates must be checked in the original figures and notes. PDF text extraction may merge columns, omit images, skip empty text pages or distort reading order; verify original pages. Server Last-Modified does not prove immutable historical archive. Check ILO licensing before reuse.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('keyword')
    p.add_argument('--start-page', type=int, default=1)
    p.add_argument('--end-page', type=int, default=84)
    p.add_argument('--limit', type=int, default=20)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.start_page, a.end_page, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
