"""Saint Kitts and Nevis official GDP tables for 2015–2023."""
import release_runtime
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.stats.gov.kn/topics/economic-statistics/national-accounts-balance-of-payments/'
PATHS = {'constant': 'gross-domestic-product-by-economic-activity-at-constant-2006-basic-prices-ec-millions-2015-to-2023', 'current': 'gross-domestic-product-by-economic-activity-at-current-basic-prices-ec-millions-2015-2023/'}

def table(price='constant'):
    if price not in PATHS:
        raise ValueError('price must be current or constant')
    url = BASE + PATHS[price]
    with requests.get(url, timeout=30, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for part in r.iter_content(65536):
            raw.extend(part)
            if len(raw) > 3000000:
                raise ValueError('Page exceeds size limit')
        modified = r.headers.get('Last-Modified')
    soup = BeautifulSoup(bytes(raw), 'html.parser')
    tables = soup.find_all('table')
    if len(tables) != 1:
        raise ValueError('Unexpected table count')
    rows = []
    for tr in tables[0].find_all('tr'):
        row = [{'text': c.get_text(' ', strip=True), 'tag': c.name, 'rowspan': c.get('rowspan', '1'), 'colspan': c.get('colspan', '1'), 'class': c.get('class', []), 'style': c.get('style', '')} for c in tr.find_all(['th', 'td'], recursive=False)]
        if row:
            rows.append(row)
    if not rows or [c['text'] for c in rows[0]][1:] != [str(y) for y in range(2015, 2024)]:
        raise ValueError('Unexpected table periods')
    return {'source': url, 'price': price, 'last_modified_header': modified, 'title': soup.title.get_text(' ', strip=True) if soup.title else '', 'rows': rows, 'notes': ['Source: Saint Kitts and Nevis Department of Statistics. Table is by economic activity at basic prices, with a separate GDP at market prices row.', 'Level values use millions of Eastern Caribbean dollars; per-capita rows in the current-price table use EC$ or US$ as explicitly labeled. Growth rows are percentages.', 'Constant-price series base is 2006. Source hyphens, empty values, unit labels, periods, dates, parent-child categories and source notes are retained; do not treat missing marks as zero.', 'Source pages can be revised; stated dates are table metadata and do not by themselves prove the current version available at a prior cutoff.']}
