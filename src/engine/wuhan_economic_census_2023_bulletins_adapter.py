"""Official Wuhan fifth economic census bulletins, including raw HTML tables."""
import release_runtime
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
BASE = 'https://tjj.wuhan.gov.cn/tjfw/wjptjgb/202506/'
IDS = {1: (9, 2592791), 2: (18, 2596867), 3: (18, 2596973), 4: (18, 2596984), 5: (18, 2597000), 6: (18, 2596954), 7: (18, 2596943)}

def bulletin(number):
    if isinstance(number, bool) or not isinstance(number, int) or number not in IDS:
        raise ValueError('bulletin number must be 1 through 7')
    day, ident = IDS[number]
    url = BASE + f't202506{day:02d}_{ident}.shtml'
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    body = BeautifulSoup(response.content, 'html.parser').select_one('.TRS_UEDITOR')
    if not body or not body.get_text(strip=True):
        raise ValueError('official article body missing')
    tables = []
    for table in body.find_all('table'):
        rows = []
        for tr in table.find_all('tr'):
            cells = [{'text': cell.get_text(' ', strip=True), 'rowspan': int(cell.get('rowspan', 1)), 'colspan': int(cell.get('colspan', 1))} for cell in tr.find_all(['td', 'th'], recursive=False)]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    return {'census_year': 2023, 'bulletin_number': number, 'source': '武汉市统计局', 'source_url': url, 'text': body.get_text('\n', strip=True), 'tables': tables, 'image_urls': [urljoin(url, img['src']) for img in body.find_all('img', src=True)]}
