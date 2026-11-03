"""European Court of Human Rights annual judgments by respondent state, 2024–2025."""
import release_runtime
import argparse, io, json, re, requests
from pypdf import PdfReader
URLS = {2024: 'https://www.echr.coe.int/documents/d/echr/stats-violation-2024-eng', 2025: 'https://www.echr.coe.int/documents/d/echr/stats-violation-2025-eng'}
INFO = 'https://www.echr.coe.int/statistical-reports'

def query(state, year, local_file=None):
    if not isinstance(state, str) or not state.strip() or len(state) > 100 or (year not in URLS):
        raise ValueError('invalid state or year')
    if local_file:
        reader = PdfReader(local_file)
    else:
        r = requests.get(URLS[year], timeout=40)
        r.raise_for_status()
        if len(r.content) > 3000000 or not r.content.startswith(b'%PDF-'):
            raise ValueError('unexpected PDF')
        reader = PdfReader(io.BytesIO(r.content))
    if len(reader.pages) != 2:
        raise ValueError('unexpected report page count')
    first = (reader.pages[0].extract_text() or '')[:100]
    if str(year) not in first and ''.join((ch * 2 for ch in str(year))) not in first:
        raise ValueError('report year mismatch')
    lines = []
    for page in reader.pages:
        lines.extend((page.extract_text() or '').splitlines())
    pattern = re.compile('^' + re.escape(state.strip()) + '\\s+(\\d+)(?:\\s|$)', re.IGNORECASE)
    matches = [(n, m.group(1)) for n, l in enumerate(lines) if (m := pattern.match(l.strip()))]
    if len(matches) > 1:
        raise ValueError('ambiguous state row')
    return {'provider': None if local_file else 'European Court of Human Rights', 'source': local_file if local_file else URLS[year], 'documentation': INFO, 'year': year, 'state': state.strip(), 'total_judgments': int(matches[0][1]) if matches else None, 'unit': None if local_file else 'judgments', 'note': 'Extracts only the first total judgments field from the annual report row; no matching numeric row is null, not zero. Counts are judgments against the respondent state, not number of applications or proof that every judgment found a violation; a judgment may address multiple applications or states. Source PDF metadata can be updated.' + (' Local PDF provenance and table meaning are unverified; the page and year checks alone do not establish authenticity.' if local_file else '')}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('state')
    p.add_argument('year', type=int, choices=[2024, 2025])
    p.add_argument('--local-file')
    a = p.parse_args()
    print(json.dumps(query(a.state, a.year, a.local_file), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
