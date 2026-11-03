"""UN 2023 SDG statistical annex PDF, released as a separate file."""
import release_runtime
import argparse, concurrent.futures, hashlib, json, os, tempfile
from pathlib import Path
import requests
from pypdf import PdfReader
URL = 'https://unstats.un.org/sdgs/files/report/2023/E_2023_64_Statistical_Annex_I_and_II.pdf'
PAGE = 'https://unstats.un.org/sdgs/report/2023/'
SIZE = 7277694
BLOCK = 1048576
SHA = '26808dd334efa50efd96d933a7fb47f10740041e2eec2c4389e07a0ded56f9c1'
CACHE = release_runtime.home() / '.cache' / 'zju-research-toolkit' / 'UN_SDG_2023_Statistical_Annex.pdf'

def _hash(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda: f.read(1048576), b''):
            h.update(c)
    return h.hexdigest()

def _pdf():
    if CACHE.is_file() and _hash(CACHE) == SHA:
        return CACHE
    if CACHE.exists():
        raise ValueError('existing cache checksum mismatch; review manually')
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    tmp = None

    def part(i):
        a = i * BLOCK
        b = min(a + BLOCK, SIZE) - 1
        r = requests.get(URL, headers={'Range': f'bytes={a}-{b}'}, timeout=40)
        r.raise_for_status()
        if r.status_code != 206 or r.headers.get('Content-Range') != f'bytes {a}-{b}/{SIZE}' or len(r.content) != b - a + 1:
            raise ValueError('invalid range or file changed')
        return r.content
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            with tempfile.NamedTemporaryFile(dir=CACHE.parent, prefix='.sdg-', delete=False) as f:
                tmp = Path(f.name)
                for chunk in pool.map(part, range((SIZE + BLOCK - 1) // BLOCK)):
                    f.write(chunk)
        if _hash(tmp) != SHA:
            raise ValueError('source checksum changed; review manually')
        os.replace(tmp, CACHE)
        return CACHE
    finally:
        if tmp and tmp.exists():
            tmp.unlink()

def query(keyword='', start_page=1, end_page=30, limit=20):
    if not isinstance(keyword, str) or len(keyword) > 100 or any((type(x) is not int for x in (start_page, end_page, limit))) or (not 1 <= start_page <= end_page <= 313) or (end_page - start_page > 99) or (not 1 <= limit <= 100):
        raise ValueError('invalid query')
    r = PdfReader(str(_pdf()))
    if len(r.pages) != 313:
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
    return {'source': URL, 'report_page': PAGE, 'edition': '2023 statistical annex E/2023/64', 'main_report_date': '2023-07-10', 'pdf_creation_date_raw': str(r.metadata.get('/CreationDate', '')), 'pdf_modification_date_raw': str(r.metadata.get('/ModDate', '')), 'observed_http_last_modified': 'Mon, 26 Jun 2023 20:18:44 GMT', 'source_sha256': SHA, 'matches_in_page_range': len(out), 'empty_text_pages': empty, 'results': out[:limit], 'note': 'UN Secretary-General statistical annex: main report date differs from annex file modification date. Data may be estimates, have different years, units and sources; check indicator title and table notes, including previous page. PDF extraction may mix columns and omit charts. File timestamps do not independently establish historical immutability. PDF cached locally (~7.3 MB), checksum pinned.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--keyword', default='')
    p.add_argument('--start-page', type=int, default=1)
    p.add_argument('--end-page', type=int, default=30)
    p.add_argument('--limit', type=int, default=20)
    a = p.parse_args()
    print(json.dumps(query(a.keyword, a.start_page, a.end_page, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
