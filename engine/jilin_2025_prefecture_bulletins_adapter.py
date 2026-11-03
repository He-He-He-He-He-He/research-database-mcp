"""Selected 2025 provincial and prefecture statistical bulletins on Jilin bureau website."""
import release_runtime
import requests
from bs4 import BeautifulSoup
BASE = 'https://tjj.jl.gov.cn/tjsj/tjgb/ndgb/'
ITEMS = {'吉林省': ('20260427', '3627028'), '吉林市': ('20260825', '3665455'), '长春市': ('20260909', '3669193'), '通化市': ('20260908', '3668976'), '松原市': ('20260907', '3668534'), '辽源市': ('20260907', '3668517'), '四平市': ('20260908', '3668990'), '白城市': ('20260907', '3668501'), '延边朝鲜族自治州': ('20260908', '3668981'), '白山市': ('20260907', '3668512')}

def _url(region):
    if region not in ITEMS:
        raise ValueError('region must be listed by catalog()')
    date, id = ITEMS[region]
    return f'{BASE}{date[:6]}/t{date}_{id}.html'

def catalog():
    return {'source': '吉林省统计局', 'year': 2025, 'items': [{'region': n, 'url': _url(n)} for n in ITEMS]}

def bulletin(region):
    url = _url(region)
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    body = s.select_one('#content .TRS_UEDITOR')
    if body is None:
        raise ValueError('official bulletin body not found')
    tables = []
    for t in body.find_all('table'):
        rows = []
        for tr in t.find_all('tr'):
            cells = [{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    return {'source': '吉林省统计局', 'region': region, 'year': 2025, 'url': url, 'article_text': body.get_text('\n', strip=True), 'tables': tables}
