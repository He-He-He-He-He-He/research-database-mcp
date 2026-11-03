"""ILO 2024–26 World Social Protection Report: social security convention table."""
import release_runtime
import argparse, hashlib, json
import requests
from bs4 import BeautifulSoup
URL = 'https://webapps.ilo.org/static/english/reports/flagship/world_social_protection_report_2024-26/Annex.html'
PAGE = 'https://www.ilo.org/publications/flagship-reports/world-social-protection-report-2024-26-universal-social-protection-climate'

def query(keyword='', limit=50):
    if not isinstance(keyword, str) or len(keyword) > 100 or type(limit) is not int or (not 1 <= limit <= 300):
        raise ValueError('invalid query')
    with requests.get(URL, stream=True, timeout=30) as r:
        r.raise_for_status()
        modified = r.headers.get('Last-Modified')
        raw = r.raw.read(2000001, decode_content=True)
    if len(raw) > 2000000:
        raise ValueError('page exceeds limit')
    s = BeautifulSoup(raw, 'html.parser')
    found = []
    for t in s.select('table'):
        h = t.find_previous(['h3', 'h4'])
        if h and 'Ratification of up-to-date ILO social security Conventions' in h.get_text(' ', strip=True):
            found.append((h, t))
    if len(found) != 1:
        raise ValueError('unexpected table structure')
    heading, t = found[0]

    def cells(tr):
        return [{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['th', 'td'], recursive=False)]
    trs = t.select('tr')
    headers = [cells(x) for x in trs[:2]]
    rows = []
    for i, tr in enumerate(trs[2:], start=3):
        row = cells(tr)
        if row and keyword.casefold() in row[0]['text'].casefold():
            rows.append({'source_row': i, 'cells': row})
    p = t.find_next('p', class_='Source')
    notes = []
    if p:
        for node in [p, *p.find_all_next(['p', 'h3', 'h4'])]:
            if node.name in ('h3', 'h4'):
                break
            if node.get('class') and 'Source' in node.get('class'):
                notes.append(node.get_text(' ', strip=True))
    return {'source': URL, 'report_page': PAGE, 'report_publication_date': '2024-09-12', 'http_last_modified': modified, 'page_sha256': hashlib.sha256(raw).hexdigest(), 'heading': heading.get_text(' ', strip=True), 'headers': headers, 'matched_count': len(rows), 'rows': rows[:limit], 'notes': notes, 'note': 'Historical ILO report annex, not a live treaty register or confirmation of present legal effect. Some footnotes specify future entry into force; dates in cells are not automatically effective dates. Preserve multi-row header, branch specificity and all notes. Empty cells must not be interpreted as definitive non-ratification. Online page may have been modified since report publication; consult authoritative treaty register for current status.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--keyword', default='')
    p.add_argument('--limit', type=int, default=50)
    a = p.parse_args()
    print(json.dumps(query(a.keyword, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
