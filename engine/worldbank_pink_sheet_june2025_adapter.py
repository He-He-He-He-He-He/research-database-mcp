"""World Bank Pink Sheet June 3, 2025, original historical PDF text search."""
import release_runtime
import argparse
import io
import json
import requests
from pypdf import PdfReader
URL = 'https://thedocs.worldbank.org/en/doc/18675f1d1639c7a34d463f59263ba0a2-0050012025/related/CMO-Pink-Sheet-June-2025.pdf'
MAX_BYTES = 2000000

def search(keyword, limit=20):
    if not isinstance(keyword, str) or not 2 <= len(keyword.strip()) <= 100 or (not isinstance(limit, int)) or isinstance(limit, bool) or (not 1 <= limit <= 100):
        raise ValueError('invalid keyword or limit')
    with requests.get(URL, timeout=30, stream=True) as response:
        response.raise_for_status()
        raw = bytearray()
        for block in response.iter_content(65536):
            raw.extend(block)
            if len(raw) > MAX_BYTES:
                raise ValueError('PDF exceeds size limit')
    reader = PdfReader(io.BytesIO(raw))
    results = []
    total = 0
    if len(reader.pages) != 3:
        raise ValueError('unexpected PDF page count; check upstream file')
    for page_no, page in enumerate(reader.pages, 1):
        lines = page.extract_text().splitlines()
        for n, line in enumerate(lines):
            if keyword.casefold() not in line.casefold():
                continue
            total += 1
            if len(results) < limit:
                results.append({'page': page_no, 'line_number': n + 1, 'line': line, 'previous_line': lines[n - 1] if n else None, 'next_line': lines[n + 1] if n + 1 < len(lines) else None})
    return {'source': URL, 'provider': 'World Bank', 'publication_date': '2025-06-03', 'release': 'June 2025 Pink Sheet', 'query': keyword, 'total_matches': total, 'returned': len(results), 'results': results, 'note': 'Raw PDF text, not parsed numeric observations. Table rows can wrap and values can be misaligned; inspect the original PDF. Page 1–2 have mixed annual, quarterly and monthly periods; May 2025 is latest monthly column. Page 3 defines price series.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('keyword')
    p.add_argument('--limit', type=int, default=20)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
