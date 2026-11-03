"""Yunnan provincial statistical bureau fifth economic census bulletins."""
import release_runtime
import requests
from bs4 import BeautifulSoup
BASE = 'https://stats.yn.gov.cn/zwgk/zfxxgk/fdzdgknr/tjsj/tjgb/202502/t20250218_'
IDS = {2: 1204490, 3: 1204497, 4: 1204507, 5: 1204516, 6: 1204522, 7: 1204530}
TOPICS = {2: '单位基本情况', 3: '第二产业', 4: '第三产业之一', 5: '第三产业之二', 6: '部分新兴产业', 7: '分地区单位和从业人员'}

def catalog():
    return {'source': '云南省统计局', 'census': '第五次全国经济普查', 'items': [{'number': n, 'topic': TOPICS[n], 'url': f'{BASE}{i}.html'} for n, i in IDS.items()]}

def bulletin(number):
    if isinstance(number, bool) or number not in IDS:
        raise ValueError('number must be 2–7')
    url = f'{BASE}{IDS[number]}.html'
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    body = s.select_one('.acticle-content')
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
    return {'source': '云南省统计局', 'census': '第五次全国经济普查', 'number': number, 'topic': TOPICS[number], 'url': url, 'article_text': body.get_text('\n', strip=True), 'tables': tables}
