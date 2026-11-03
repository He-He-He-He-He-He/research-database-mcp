"""Saint Lucia CSO current and constant-price annual GDP tables."""
import release_runtime
import requests
from bs4 import BeautifulSoup
BASE = 'https://stats.gov.lc/subjects/economy/national-accounts/'
PAGES = {'current': 'annual-gross-domestic-product-economic-activity-at-current-prices-2006-to-2025/', 'constant': 'annual-gross-domestic-product-by-economic-activity-at-constant-prices-2006-to-2025/'}

def table(price='current'):
    if price not in PAGES:
        raise ValueError('price must be current or constant')
    url = BASE + PAGES[price]
    with requests.get(url, timeout=30, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for x in r.iter_content(65536):
            raw.extend(x)
            if len(raw) > 3000000:
                raise ValueError('Page too large')
        modified = r.headers.get('Last-Modified')
    s = BeautifulSoup(bytes(raw), 'html.parser')
    tables = s.find_all('table')
    if len(tables) != 1:
        raise ValueError('Expected exactly one table; source changed')
    rows = []
    for tr in tables[0].find_all('tr'):
        cells = []
        for c in tr.find_all(['th', 'td'], recursive=False):
            cells.append({'text': c.get_text(' ', strip=True), 'tag': c.name, 'rowspan': c.get('rowspan', '1'), 'colspan': c.get('colspan', '1'), 'class': c.get('class', []), 'style': c.get('style', '')})
        if cells:
            rows.append(cells)
    if not rows or not any((c['text'] == '2025' for c in rows[0])):
        raise ValueError('Unexpected table header')
    return {'source': url, 'price': price, 'title': s.title.get_text(' ', strip=True) if s.title else '', 'last_modified_header': modified, 'rows': rows, 'notes': ['Central Statistical Office source; original row order, repeated row labels, percentages, empty strings and textual numbers are retained.', 'Current and constant price series are different. Currency unit and constant-price base were not verified on this page; consult official metadata before interpretation.', 'Source row contains date 04/09/26, preserved literally without assuming date format; current website values are revised and not historical-vintage evidence.', 'GDP at market prices differs from gross value added at basic prices and their separate growth rates; do not combine hierarchical rows.']}
