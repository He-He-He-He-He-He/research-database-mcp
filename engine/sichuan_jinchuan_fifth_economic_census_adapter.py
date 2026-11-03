"""Jinchuan County, Sichuan fifth economic census official bulletins."""
import release_runtime
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.abjinchuan.gov.cn/jinchuanxian/c100053/202509/'
IDS = {1: '9dcc371a6d0f4fe3a25a80f10380116c', 2: 'dfad738fc8c249bd8ab3ede28c468818', 3: 'd90a30c7f2fd469ea798f6e142f02800', 4: '7f99286f9ea1431f9ae349c19e7c810c', 5: '218b7b6390634171a37e777210b35524', 6: '7b64429d4dd04b9db45f6e49f40d6ce5'}
TOPICS = {1: '普查概述', 2: '单位基本情况', 3: '第二产业', 4: '第三产业之一', 5: '第三产业之二', 6: '新兴产业'}

def catalog():
    return {'source': '金川县人民政府', 'region': '四川省阿坝州金川县', 'census': '第五次全国经济普查', 'items': [{'number': n, 'topic': TOPICS[n], 'url': BASE + i + '.shtml'} for n, i in IDS.items()]}

def bulletin(number):
    if isinstance(number, bool) or number not in IDS:
        raise ValueError('number must be 1–6')
    url = BASE + IDS[number] + '.shtml'
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    body = s.select_one('.common_detail')
    if body is None:
        raise ValueError('official article body missing')
    tables = []
    for t in body.find_all('table'):
        rows = []
        for tr in t.find_all('tr'):
            cells = [{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    return {'source': '金川县人民政府', 'region': '四川省阿坝州金川县', 'number': number, 'topic': TOPICS[number], 'url': url, 'article_text': body.get_text('\n', strip=True), 'tables': tables, 'source_note': '第三号工业企业内资数据正文与表3-1不一致，请以官方澄清为准'}
