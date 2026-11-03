"""Wuhan seventh national population census official bulletins and tables."""
import release_runtime
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
BASE = 'https://tjj.wuhan.gov.cn/tjfw/tjgb/202105/'
IDS = {1: 1707390, 2: 1707395, 3: 1707398, 4: 1707401, 5: 1707414, 6: 1707417}

def bulletin(number):
    if not isinstance(number, int) or number not in IDS:
        raise ValueError('bulletin number must be 1 through 6')
    url = BASE + f't20210528_{IDS[number]}.shtml'
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    body = s.select_one('.TRS_UEDITOR')
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
    return {'census_year': 2020, 'bulletin_number': number, 'source': '武汉市统计局', 'source_url': url, 'text': body.get_text('\n', strip=True), 'tables': tables, 'image_urls': [urljoin(url, x['src']) for x in body.find_all('img', src=True)]}
