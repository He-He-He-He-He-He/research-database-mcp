"""WHO World Health Statistics 2024 report PDF search."""
import release_runtime
import argparse, hashlib, json, os, tempfile
from pathlib import Path
import requests
from pypdf import PdfReader
URL = 'https://iris.who.int/server/api/core/bitstreams/74b12494-f213-4b5b-9533-18442147e1fb/content'
PAGE = 'https://www.who.int/southeastasia/publications/i/item/9789240094703'
SHA = 'f7b08734131ff6b3e07a508f2efc12a94c85ce19eaee2a98f0bbc57fad3c3555'
CACHE = release_runtime.home() / '.cache' / 'zju-research-toolkit' / 'WHO_WHS2024.pdf'

def _hash(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda: f.read(1048576), b''):
            h.update(c)
    return h.hexdigest()

def _pdf():
    if CACHE.is_file() and _hash(CACHE) == SHA:
        return CACHE
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(dir=CACHE.parent, prefix='.who-whs2024-', delete=False) as f:
            temp = Path(f.name)
            size = 0
            with requests.get(URL, stream=True, timeout=90) as r:
                r.raise_for_status()
                for c in r.iter_content(1048576):
                    size += len(c)
                    if size > 45000000:
                        raise ValueError('PDF exceeds limit')
                    f.write(c)
        if _hash(temp) != SHA:
            raise ValueError('source PDF checksum changed; manual review required')
        os.replace(temp, CACHE)
        return CACHE
    finally:
        if temp and temp.exists():
            temp.unlink()

def query(keyword='', start_page=1, end_page=50, limit=20):
    if not isinstance(keyword, str) or len(keyword) > 100 or any((type(x) is not int for x in (start_page, end_page, limit))) or (not 1 <= start_page <= end_page <= 96) or (end_page - start_page > 99) or (not 1 <= limit <= 100):
        raise ValueError('invalid query')
    r = PdfReader(str(_pdf()))
    if len(r.pages) != 96:
        raise ValueError('unexpected page count')
    out = []
    empty = []
    for i in range(start_page - 1, end_page):
        text = r.pages[i].extract_text() or ''
        lines = text.splitlines()
        if not lines:
            empty.append(i + 1)
        if not keyword:
            out.append({'pdf_page': i + 1, 'text': text})
        else:
            for j, line in enumerate(lines):
                if keyword.casefold() in line.casefold():
                    out.append({'pdf_page': i + 1, 'line': line, 'context': lines[max(0, j - 2):j + 5]})
    return {'source': URL, 'report_page': PAGE, 'edition': '2024', 'report_publication_date': '2024-05-21', 'http_last_modified_observed': '2025-09-19T02:14:25Z', 'pdf_creation_date_raw': str(r.metadata.get('/CreationDate', '')), 'pdf_modification_date_raw': str(r.metadata.get('/ModDate', '')), 'source_sha256': SHA, 'matches_in_page_range': len(out), 'empty_text_pages': empty, 'results': out[:limit], 'note': 'WHO World Health Statistics 2024 report, distinct from the separately published country workbook already supported in this toolkit. WHO describes the report as 86 pages while this PDF has 96 physical pages including front matter; output uses physical page numbers. PDF metadata and 2025 server modification postdate 2024 report publication and do not establish current bytes as original or immutable. Distinguish model estimates from observations, reference years, denominators and uncertainty. Text may misalign tables or omit charts and notes; verify source page. CC BY-NC-SA 3.0 IGO applies. Cached download approximately 4.5 MiB; checksum pinned.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--keyword', default='')
    p.add_argument('--start-page', type=int, default=1)
    p.add_argument('--end-page', type=int, default=50)
    p.add_argument('--limit', type=int, default=20)
    a = p.parse_args()
    print(json.dumps(query(a.keyword, a.start_page, a.end_page, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
