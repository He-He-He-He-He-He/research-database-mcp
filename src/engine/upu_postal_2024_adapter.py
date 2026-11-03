"""UPU Postal Statistics 2024: official country pages with column-preserving text."""
import release_runtime
import re
import requests
from pypdf import PdfReader
URL = 'https://www.upu.int/UPU/media/upu/publications/202512postalStatistics2024MainReport_EN_FR.pdf'
DOC = 'https://www.upu.int/en/Universal-Postal-Union/Activities/Research-Publications/Postal-Statistics'

def download(path):
    r = requests.get(URL, timeout=120)
    r.raise_for_status()
    if not r.content.startswith(b'%PDF-'):
        raise ValueError('source did not return a PDF')
    with open(path, 'xb') as f:
        f.write(r.content)
    return {'source': URL, 'file': path, 'bytes': len(r.content), 'note': 'Official 2024 edition; existing file is not overwritten.'}

def _catalog(reader):
    if len(reader.pages) != 533 or 'Postal Statistics 2024' not in reader.pages[0].extract_text():
        raise ValueError('not the expected 2024 report edition')
    result = []
    for page in (11, 12):
        for line in reader.pages[page].extract_text().splitlines():
            m = re.match('^([A-Z]{2})\\s+(.+?)\\s*\\.{3,}.*?\\s+(\\d+)\\s*$', line)
            if m:
                result.append({'code': m.group(1), 'name': m.group(2).strip(), 'printed_page': int(m.group(3))})
    if len(result) != 186 or len({x['code'] for x in result}) != 186:
        raise ValueError('unexpected contents layout')
    return result

def catalog(path, keyword=''):
    with open(path, 'rb') as f:
        rows = _catalog(PdfReader(f))
        selected = [x for x in rows if not keyword or keyword.casefold() in (x['code'] + ' ' + x['name']).casefold()]
    return {'source': str(path), 'reference_source': URL, 'document': DOC, 'edition': None, 'expected_edition': '2024', 'total_countries': len(rows), 'rows': selected, 'note': 'Local PDF provenance and edition are unverified despite layout checks. Printed page refers to the source report; records do not establish current data or completeness.'}

def country(path, code):
    if not isinstance(code, str) or not re.fullmatch('[A-Za-z]{2}', code):
        raise ValueError('country code must be two letters')
    with open(path, 'rb') as f:
        reader = PdfReader(f)
        found = [x for x in _catalog(reader) if x['code'] == code.upper()]
        if not found:
            raise ValueError('country not in report contents')
        row = found[0]
        index = row['printed_page'] + 57
        texts = [reader.pages[i].extract_text(extraction_mode='layout') for i in (index, index + 1)]
        if not texts[0].lstrip().startswith(code.upper() + ' '):
            raise ValueError('country page verification failed')
        return {'source': str(path), 'reference_source': URL, 'document': DOC, 'country': row, 'edition': None, 'expected_edition': '2024', 'pdf_pages': [index + 1, index + 2], 'layout_text': texts, 'notes': ['Local PDF provenance and edition are unverified despite layout checks.', 'Bilingual pages preserve five annual columns and original unit labels, but PDF text extraction may misalign columns or wrapped headings; verify source pages before quoting.', 'The 2024 edition can include older observations, missing values, preliminary figures and currency values in SDR; inspect column year, operator coverage and technical notes.', 'Sections 3–12 concern designated postal operators; they are not necessarily all providers or the entire postal market.']}
