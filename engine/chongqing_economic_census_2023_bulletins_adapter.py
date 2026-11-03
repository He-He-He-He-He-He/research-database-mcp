"""Chongqing fifth economic census bulletins and HTML tables."""
import release_runtime
import requests
from bs4 import BeautifulSoup
BASE = 'https://tjj.cq.gov.cn/zwgk_233/fdzdgknr/tjxx/sjzl_55471/tjgb_55472/202503/'
IDS = {1: 14427376, 2: 14427427, 3: 14427445, 4: 14427501, 5: 14427572, 6: 14427606, 7: 14427613}

def bulletin(number):
    if not isinstance(number, int) or number not in IDS:
        raise ValueError('bulletin number must be 1 through 7')
    url = BASE + f't20250321_{IDS[number]}.html'
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    body = s.select_one('.trs_editor_view')
    if not body:
        raise ValueError('article body missing')
    tables = []
    for t in body.find_all('table'):
        rows = []
        for tr in t.find_all('tr'):
            cells = [{'text': c.get_text('', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    return {'census_year': 2023, 'bulletin_number': number, 'source': '重庆市统计局', 'source_url': url, 'text': body.get_text('\n', strip=True), 'tables': tables}
