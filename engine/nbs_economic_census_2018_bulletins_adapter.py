"""Fourth national economic census bulletins and HTML tables, NBS."""
import release_runtime
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.stats.gov.cn/sj/zxfb/202302/'

def bulletin(number):
    if not isinstance(number, int) or number not in range(1, 8):
        raise ValueError('bulletin number must be 1 through 7')
    url = BASE + f't20230203_{1900523 + number}.html'
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, 'html.parser')
    body = soup.select_one('.trs_editor_view') or soup.select_one('.txt-content') or soup.select_one('.TRS_Editor')
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
    return {'census_year': 2018, 'bulletin_number': number, 'source': '国家统计局', 'source_url': url, 'text': body.get_text('\n', strip=True), 'tables': tables}
