"""Dominica CSO constant-market-price GDP 2000–2020 as source strings."""
import release_runtime
import requests
from bs4 import BeautifulSoup
URL = 'https://stats.gov.dm/subjects/economic-indicators/gross-domestic-product-in-constant-market-prices-2000-to-2018/'
PAGE = 'https://stats.gov.dm/subjects/economic-indicators/'

def table():
    with requests.get(URL, timeout=30, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for chunk in r.iter_content(65536):
            raw.extend(chunk)
            if len(raw) > 2000000:
                raise ValueError('Page too large')
        modified = r.headers.get('Last-Modified')
    soup = BeautifulSoup(bytes(raw), 'html.parser')
    tables = soup.find_all('table')
    if len(tables) != 1:
        raise ValueError('Unexpected table count')
    rows = []
    for tr in tables[0].find_all('tr'):
        row = [{'text': c.get_text(' ', strip=True), 'tag': c.name, 'rowspan': c.get('rowspan', '1'), 'colspan': c.get('colspan', '1')} for c in tr.find_all(['th', 'td'], recursive=False)]
        if row:
            rows.append(row)
    if not rows or [x['text'] for x in rows[0]] != ['YEAR', 'GDP']:
        raise ValueError('Unexpected table header')
    return {'source': URL, 'source_page': PAGE, 'title': soup.title.get_text(' ', strip=True) if soup.title else '', 'last_modified_header': modified, 'rows': rows, 'notes': ['GDP at constant market prices, not GVA or nominal GDP. Source column 2020P retains its suffix; verify its definition in source metadata.', 'Currency, magnitude and base year are not established on this table page; do not compare or label units without further verification.', 'The URL includes 2018 but title and data extend to 2020; retain actual rows and source labels.', 'Current website data may have been revised; no historical public availability is inferred.']}
