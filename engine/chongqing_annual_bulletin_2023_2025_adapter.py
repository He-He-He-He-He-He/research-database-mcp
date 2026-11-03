"""Chongqing annual socio-economic statistical bulletins, 2023–2025."""
import release_runtime
import requests
from bs4 import BeautifulSoup
URLS = {2023: 'https://tjj.cq.gov.cn/zwgk_233/fdzdgknr/tjxx/sjzl_55471/tjgb_55472/202403/t20240326_13084652.html', 2024: 'https://tjj.cq.gov.cn/zwgk_233/fdzdgknr/tjxx/sjzl_55471/tjgb_55472/202503/t20250326_14443791.html', 2025: 'https://tjj.cq.gov.cn/zwgk_233/fdzdgknr/tjxx/sjjd_55469/202603/t20260326_15568538.html'}

def bulletin(year):
    if year not in URLS:
        raise ValueError('available years: 2023, 2024, 2025')
    url = URLS[year]
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
    if not tables:
        raise ValueError('no HTML tables found')
    return {'year': year, 'source': '重庆市统计局', 'source_url': url, 'text': body.get_text('\n', strip=True), 'tables': tables}
