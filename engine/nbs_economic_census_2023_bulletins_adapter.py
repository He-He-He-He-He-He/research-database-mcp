"""The fifth national economic census official bulletins and HTML tables."""
import release_runtime
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.stats.gov.cn/zt_18555/zthd/lhfw/2025/2025_zgjjpc/202502/'
NUMBERS = {1: 1958633, 2: 1958632, 3: 1958631, 4: 1958630, 5: 1958629, 6: 1958628, 7: 1958627}

def bulletin(number):
    if number not in NUMBERS:
        raise ValueError('bulletin number must be 1 through 7')
    url = BASE + f't20250207_{NUMBERS[number]}.html'
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, 'html.parser')
    body = soup.select_one('.trs_editor_view')
    if not body:
        raise ValueError('article body not found')
    tables = []
    for t in body.find_all('table'):
        rows = []
        for tr in t.find_all('tr'):
            cells = [{'text': c.get_text('', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    return {'census_year': 2023, 'bulletin_number': number, 'source': '国家统计局', 'source_url': url, 'text': body.get_text('\n', strip=True), 'tables': tables}
