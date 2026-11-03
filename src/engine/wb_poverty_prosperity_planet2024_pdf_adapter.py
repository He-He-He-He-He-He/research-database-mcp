"""World Bank Poverty, Prosperity, and Planet 2024 PDF search."""
import release_runtime
import argparse, hashlib, json, os, tempfile
from pathlib import Path
import requests
from pypdf import PdfReader
URL = 'https://documents1.worldbank.org/curated/en/099101424092027337/pdf/P500855154ddde0b31827a1e9377c43d15e.pdf'
PAGE = 'https://www.worldbank.org/en/news/press-release/2024/10/15/ending-poverty-for-half-the-world-could-take-more-than-a-century'
SHA = '56927656537015cf21e75ea1d283d524ae2ed0ee59086c1b741aeb58ef809cf1'
CACHE = release_runtime.home() / '.cache' / 'zju-research-toolkit' / 'WorldBank_Poverty_Prosperity_Planet_2024.pdf'

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
        with tempfile.NamedTemporaryFile(dir=CACHE.parent, prefix='.wb-ppp2024-', delete=False) as f:
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
    if not isinstance(keyword, str) or len(keyword) > 100 or any((type(x) is not int for x in (start_page, end_page, limit))) or (not 1 <= start_page <= end_page <= 300) or (end_page - start_page > 99) or (not 1 <= limit <= 100):
        raise ValueError('invalid query')
    r = PdfReader(str(_pdf()))
    if len(r.pages) != 300:
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
    return {'source': URL, 'report_page': PAGE, 'edition': '2024', 'report_launch_date': '2024-10-15', 'http_last_modified_observed': '2026-10-30T08:31:47Z', 'pdf_creation_date_raw': str(r.metadata.get('/CreationDate', '')), 'pdf_modification_date_raw': str(r.metadata.get('/ModDate', '')), 'source_sha256': SHA, 'matches_in_page_range': len(out), 'empty_text_pages': empty, 'results': out[:limit], 'note': 'World Bank report. Report date is 2024-10-15 but the current server file reports last modified 2026-10-30; no proof this copy is identical to launch-day bytes or available before a historical cutoff. Historical thresholds such as 2.15 and 6.85 dollars use 2017 purchasing-power parity and must not be mixed with later revised thresholds. Distinguish estimates, nowcasts and projections, coverage and observation years. PDF extraction can mix table columns or omit charts and notes; verify source pages. Cached download approximately 31 MiB; checksum pinned.'}

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
