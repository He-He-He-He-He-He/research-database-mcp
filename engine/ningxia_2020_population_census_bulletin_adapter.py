"""Ningxia 2020 population census bulletins from provincial statistical bureau."""
import release_runtime
import requests
from bs4 import BeautifulSoup
BASE = 'https://tj.nx.gov.cn/zzb/tjgb/202105/t20210525_'
IDS = {1: 2854292, 2: 2854299, 3: 2854332, 4: 2854368, 5: 2857657, 6: 2857846}
TOPICS = {1: '全区人口', 2: '地区人口', 3: '性别构成', 4: '年龄构成', 5: '受教育情况', 6: '城乡及流动人口'}

def catalog():
    return {'source': '宁夏回族自治区统计局', 'census': '第七次全国人口普查', 'items': [{'number': n, 'topic': TOPICS[n], 'url': f'{BASE}{i}.html'} for n, i in IDS.items()]}

def bulletin(number):
    if isinstance(number, bool) or number not in IDS:
        raise ValueError('number must be 1–6')
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
    return {'source': '宁夏回族自治区统计局', 'census': '第七次全国人口普查', 'number': number, 'topic': TOPICS[number], 'url': url, 'article_text': body.get_text('\n', strip=True), 'tables': tables}
