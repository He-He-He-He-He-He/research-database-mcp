"""Jilin statistical bureau fifth economic census bulletins and HTML tables."""
import release_runtime
import requests
from bs4 import BeautifulSoup
BASE = 'https://tjj.jl.gov.cn/tjsj/tjgb/pcjqtgb/202504/t20250422_'
IDS = {1: 3449638, 2: 3449637, 3: 3449636, 4: 3449633, 5: 3449632}
TOPICS = {1: '单位基本情况', 2: '第二产业', 3: '第三产业之一', 4: '第三产业之二', 5: '部分新兴产业'}

def catalog():
    return {'source': '吉林省统计局', 'census': '第五次全国经济普查', 'items': [{'number': n, 'topic': TOPICS[n], 'url': f'{BASE}{i}.html'} for n, i in IDS.items()]}

def bulletin(number):
    if isinstance(number, bool) or number not in IDS:
        raise ValueError('number must be 1–5')
    url = f'{BASE}{IDS[number]}.html'
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    body = s.select_one('#content .TRS_Editor')
    if body is None:
        raise ValueError('Official article content not found')
    tables = []
    for t in body.find_all('table'):
        rows = []
        for tr in t.find_all('tr'):
            cells = [{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    if not tables:
        raise ValueError('No tables found on official page')
    return {'source': '吉林省统计局', 'census': '第五次全国经济普查', 'number': number, 'topic': TOPICS[number], 'url': url, 'article_text': body.get_text('\n', strip=True), 'tables': tables}
