"""UNODC Global Report on Trafficking in Persons 2024 PDF search (HRB hosted)."""
import release_runtime
import argparse, hashlib, json, os, tempfile
from pathlib import Path
import requests
from pypdf import PdfReader
URL = 'https://www.drugsandalcohol.ie/42452/1/Globa_Report_on_Trafficking_in_Persons_2023.pdf'
PAGE = 'https://www.drugsandalcohol.ie/42452/'
SHA = 'b1e7736730a197c06cb2b62aa3f50bbc8ebc8db81248e75d7a9292420397fc7b'
CACHE = release_runtime.home() / '.cache' / 'zju-research-toolkit' / 'UNODC_Trafficking_2024_HRB.pdf'

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
        with tempfile.NamedTemporaryFile(dir=CACHE.parent, prefix='.unodc-tip2024-', delete=False) as f:
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
    if not isinstance(keyword, str) or len(keyword) > 100 or any((type(x) is not int for x in (start_page, end_page, limit))) or (not 1 <= start_page <= end_page <= 176) or (end_page - start_page > 99) or (not 1 <= limit <= 100):
        raise ValueError('invalid query')
    r = PdfReader(str(_pdf()))
    if len(r.pages) != 176:
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
    return {'source': URL, 'report_page': PAGE, 'edition': '2024', 'report_publication_month': '2024-12', 'un_presentation_date': '2024-12-12', 'http_last_modified_observed': '2024-12-17T10:48:52Z', 'pdf_creation_date_raw': str(r.metadata.get('/CreationDate', '')), 'pdf_modification_date_raw': str(r.metadata.get('/ModDate', '')), 'source_sha256': SHA, 'matches_in_page_range': len(out), 'empty_text_pages': empty, 'results': out[:limit], 'note': 'UNODC Global Report on Trafficking in Persons 2024 hosted by Irish Health Research Board. The host URL contains 2023, but report title and publisher identify the 2024 edition. Figures generally concern detected victims and cases and are not the true total trafficking prevalence; coverage and detection depend on national reporting. PDF and server dates differ from report presentation and cannot establish immutable historical bytes. PDF has font-encoding corruption on some pages: extracted text can contain wrong characters and numbers in addition to misaligned columns or missing charts/footnotes. Always verify rendered source pages. Educational/non-profit reproduction with attribution; commercial use requires prior permission. Cached download approximately 17 MiB; checksum pinned.'}

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
