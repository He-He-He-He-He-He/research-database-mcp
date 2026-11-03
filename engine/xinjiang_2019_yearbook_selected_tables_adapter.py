"""Selected official 2019 Xinjiang statistical yearbook HTML tables."""
import release_runtime
import requests
from bs4 import BeautifulSoup
BASE = 'https://tjj.xinjiang.gov.cn/tjj/'
TABLES = {'3-2': ('主要年份人口出生率、死亡率、自然增长率', 'rkjyu/202006/7780fc14ab0744579bf82301817acded.shtml'), '3-5': ('各地、州、市、县(市)户数、人口数、土地面积', 'rkjyu/202006/7d7c9aed709f42698871382ed00f2065.shtml'), '3-9': ('各地、州、市、县(市)城乡及分年龄人口', 'rkjyu/202006/5d46a49638f34b9da7f51e73cad86fcd.shtml'), '15-4': ('主要年份客运量及周转量', 'ysydc/202006/1e726a8c49a0463e903f4587d876a35d.shtml'), '15-5': ('主要年份货运量及货物周转量', 'ysydc/202006/8b18b1a2571541729943c889020bf20e.shtml')}

def catalog(keyword=''):
    return {'source': '新疆维吾尔自治区统计局', 'yearbook': 2019, 'items': [{'id': k, 'title': v[0], 'url': BASE + v[1]} for k, v in TABLES.items() if keyword in k or keyword in v[0]]}

def table(table_id):
    if table_id not in TABLES:
        raise ValueError('Unknown table ID; inspect catalog()')
    title, path = TABLES[table_id]
    url = BASE + path
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, 'html.parser')
    tables = []
    for t in soup.find_all('table'):
        rows = []
        for tr in t.find_all('tr'):
            cells = [{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    if not tables:
        raise ValueError('No HTML tables found on official page')
    return {'source': '新疆维吾尔自治区统计局', 'yearbook': 2019, 'id': table_id, 'title': title, 'url': url, 'tables': tables}
