"""Read raw current Seychelles NBS National Summary Data Page table."""
import release_runtime
import subprocess, bs4
URL = 'https://www.nbs.gov.sc/nsdp/national-summary-data-page'

def search(keyword='', offset=0, limit=20):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 50):
        raise ValueError('invalid pagination')
    p = release_runtime.run(['/usr/bin/curl', '-fsSL', '--max-time', '35', '--max-filesize', '4000000', URL], capture_output=True, timeout=40)
    if p.returncode:
        raise RuntimeError('Seychelles NBS page request failed: ' + p.stderr.decode('utf-8', 'replace').strip())
    if len(p.stdout) > 4000000:
        raise RuntimeError('Page exceeds size limit')
    doc = bs4.BeautifulSoup(p.stdout, 'html.parser')
    matches = []
    for t in doc.find_all('table'):
        rows = t.find_all('tr')
        if any(('SDDS Data Category and Component' in row.get_text(' ', strip=True) for row in rows[:10])):
            matches.append(rows)
    if len(matches) != 1:
        raise RuntimeError('Cannot identify unique NSDP table')
    rows = matches[0]
    header = next((row for row in rows[:10] if 'SDDS Data Category and Component' in row.get_text(' ', strip=True)))
    data = []
    previous = []
    for n, tr in enumerate(rows, 1):
        cells = [' '.join(c.stripped_strings) for c in tr.find_all(['td', 'th'], recursive=False)]
        if not any(cells) or tr is header:
            continue
        if not keyword or keyword.casefold() in ' '.join(cells).casefold():
            data.append({'row': n, 'cells': cells, 'previous_nonempty_rows': previous[-3:]})
        previous.append({'row': n, 'cells': cells})
    return {'source': 'National Bureau of Statistics Seychelles', 'source_page': URL, 'table_header': [' '.join(c.stripped_strings) for c in header.find_all(['td', 'th'], recursive=False)], 'keyword': keyword, 'matches': len(data), 'offset': offset, 'items': data[offset:offset + limit], 'note': 'Live summary table; retain original text, units, reference dates, signs and previous values. Previous reference date is not supplied for every row. Sections and labels may repeat; consult full source table and methodology. GDP and other figures can be revised; price indices are levels, not inflation rates.'}
