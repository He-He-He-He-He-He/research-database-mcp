"""Ningxia fourth economic census bulletins from provincial statistical bureau."""
import release_runtime
import requests
from bs4 import BeautifulSoup
BASE = 'https://tj.nx.gov.cn/zzb/tjgb/202002/t20200210_'
IDS = {1: 1948109, 2: 1948110, 3: 1948111, 4: 1948113, 5: 1948114, 6: 1948116, 7: 1948119}
TOPICS = {1: '普查概述', 2: '单位基本情况', 3: '第二产业', 4: '第三产业之一', 5: '第三产业之二', 6: '部分新兴产业', 7: '分区域单位及从业人员'}

def catalog():
    return {'source': '宁夏回族自治区统计局', 'census': '第四次全国经济普查', 'items': [{'number': n, 'topic': TOPICS[n], 'url': f'{BASE}{i}.html'} for n, i in IDS.items()]}

def bulletin(number):
    if isinstance(number, bool) or number not in IDS:
        raise ValueError('number must be 1–7')
    url = f'{BASE}{IDS[number]}.html'
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    body = s.select_one('.view.TRS_UEDITOR')
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
    return {'source': '宁夏回族自治区统计局', 'census': '第四次全国经济普查', 'number': number, 'topic': TOPICS[number], 'url': url, 'article_text': body.get_text('\n', strip=True), 'tables': tables}
