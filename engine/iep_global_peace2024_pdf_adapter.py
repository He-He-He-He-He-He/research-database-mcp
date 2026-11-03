"""Search the Institute for Economics & Peace Global Peace Index 2024 PDF."""
import release_runtime
import argparse, hashlib, io, json
import requests
from pypdf import PdfReader
URL = 'https://www.economicsandpeace.org/wp-content/uploads/2024/06/GPI-2024-web.pdf'
PAGE = 'https://www.economicsandpeace.org/report/global-peace-index-2024/'

def search(keyword, start_page=1, end_page=89, limit=20):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('invalid keyword')
    if any((type(x) is not int for x in (start_page, end_page, limit))) or not 1 <= start_page <= end_page <= 89 or (not 1 <= limit <= 100):
        raise ValueError('invalid page range or limit')
    with requests.get(URL, stream=True, timeout=40) as r:
        r.raise_for_status()
        modified = r.headers.get('Last-Modified')
        raw = r.raw.read(20000001, decode_content=True)
    if len(raw) > 20000000:
        raise ValueError('PDF exceeds size limit')
    reader = PdfReader(io.BytesIO(raw))
    if len(reader.pages) != 89:
        raise ValueError('unexpected document page count')
    hits = []
    for i in range(start_page - 1, end_page):
        lines = (reader.pages[i].extract_text() or '').splitlines()
        for n, line in enumerate(lines):
            if keyword.casefold() in line.casefold():
                hits.append({'pdf_page': i + 1, 'line': line, 'previous_line': lines[n - 1] if n else None, 'next_line': lines[n + 1] if n + 1 < len(lines) else None})
    return {'source': URL, 'report_page': PAGE, 'edition': '2024', 'http_last_modified': modified, 'source_sha256': hashlib.sha256(raw).hexdigest(), 'matches_in_page_range': len(hits), 'results': hits[:limit], 'note': 'Independent Institute for Economics & Peace composite research index, not official government statistics. Lower score indicates greater peacefulness. PDF text extraction may merge columns, omit figures or distort reading order; verify the original page visually. PDF file metadata records July 2024 and HTTP Last-Modified is not proof of an immutable historical archive. Check original source and licensing before reuse.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('keyword')
    p.add_argument('--start-page', type=int, default=1)
    p.add_argument('--end-page', type=int, default=89)
    p.add_argument('--limit', type=int, default=20)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.start_page, a.end_page, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
