"""Wuhan Statistics Bureau annual socio-economic statistical bulletins."""
import release_runtime
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
URLS = {2023: 'https://tjj.wuhan.gov.cn/tjfw/tjgb/202404/t20240405_2384677.shtml', 2024: 'https://tjj.wuhan.gov.cn/tjfw/tjgb/202503/t20250327_2558447.shtml', 2025: 'https://tjj.wuhan.gov.cn/tjfw/tjgb/202604/t20260408_2750693.shtml'}

def bulletin(year):
    if year not in URLS:
        raise ValueError('available years: 2023, 2024, 2025')
    url = URLS[year]
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    body = s.select_one('.TRS_UEDITOR')
    if body is None:
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
    images = [urljoin(url, i['src']) for i in body.find_all('img', src=True)]
    return {'year': year, 'source': '武汉市统计局', 'source_url': url, 'text': body.get_text('\n', strip=True), 'tables': tables, 'image_urls': images}
