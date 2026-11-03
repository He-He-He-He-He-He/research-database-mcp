"""International Seabed Authority exploration-contract web table."""
import release_runtime
import requests
from bs4 import BeautifulSoup
URL = 'https://isa.org.jm/Exploration%20Contracts/'

def _parse(html):
    soup = BeautifulSoup(html, 'html.parser')
    matches = []
    for table in soup.find_all('table'):
        trs = table.find_all('tr')
        if any(('CONTRACTOR' in r.get_text(' ', strip=True) and 'PMN' in r.get_text(' ', strip=True) for r in trs[:3])):
            matches.append(trs)
    if len(matches) != 1:
        raise ValueError('contract table missing or ambiguous')
    rows = []
    totals = None
    for tr in matches[0][2:]:
        cells = [x.get_text(' ', strip=True) for x in tr.find_all(['td', 'th'], recursive=False)]
        if len(cells) != 6:
            raise ValueError('unexpected contract table row')
        if cells[0].isdigit():
            rows.append(dict(zip(['number', 'contractor', 'pmn', 'sulphides', 'cfc', 'total'], cells)))
        elif not cells[0] and (not cells[1]):
            totals = dict(zip(['pmn', 'sulphides', 'cfc', 'total'], cells[2:]))
        else:
            raise ValueError('unexpected row label')
    if not rows or totals is None:
        raise ValueError('contract rows or totals missing')
    texts = list(soup.stripped_strings)
    renounced = [x for x in texts if 'CPRM renounced its rights' in x]
    narrative = [x for x in texts if 'contracts for exploration for polymetallic sulphides' in x]
    return (rows, totals, renounced, narrative)

def search(keyword='', limit=20, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 150:
        raise ValueError('invalid keyword')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or offset < 0:
        raise ValueError('invalid pagination')
    r = requests.get(URL, timeout=35)
    r.raise_for_status()
    rows, totals, footnotes, narrative = _parse(r.text)
    chosen = [x for x in rows if keyword.casefold() in x['contractor'].casefold()]
    return {'source': URL, 'last_modified_http': r.headers.get('Last-Modified'), 'total_rows': len(rows), 'matched': len(chosen), 'limit': limit, 'offset': offset, 'rows': chosen[offset:offset + limit], 'source_table_totals': totals, 'source_renunciation_notes': footnotes, 'source_narrative': narrative, 'note': 'ISA website table of historical exploration contracts, not production licences or proof of currently active rights. Source table and narrative disagree on sulphide count, and a listed contractor renounced rights; page age/status not established. Preserve empty cells as supplied and verify current contract register and official annual reports before use.'}
