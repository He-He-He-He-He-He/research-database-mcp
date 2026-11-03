"""司法部保存的 1999—2001 行政复议与应诉原表。"""
import release_runtime
import requests
from bs4 import BeautifulSoup
IDS = {1999: 396253, 2000: 396255, 2001: 396254}
TABLES = {1999: [('23个省区市收到行政复议申请', '省份'), ('23个省区市行政应诉案件审理', '审结情况')], 2000: [('省区市行政复议申请情况', '省份'), ('行政复议申请事项分类', '事项'), ('行政复议案件审理', '审理结果'), ('省区市行政应诉案件情况', '省份'), ('行政应诉案件审理', '审理情况')], 2001: [('省区市收到行政复议申请', '省份'), ('国务院部门收到行政复议申请', '部门'), ('行政复议申请事项分类', '事项'), ('行政复议案件审理', '审理结果'), ('省区市行政应诉案件情况', '省份'), ('国务院部门行政应诉案件情况', '部门'), ('省区市行政应诉案件审理', '审理情况'), ('国务院部门行政应诉案件审理', '审理情况')]}

def catalog():
    return {'source': '司法部官网保存的中国政府法制信息网历史统计', 'years': {str(y): [{'table': i + 1, 'title': v[0]} for i, v in enumerate(ts)] for y, ts in TABLES.items()}, 'note': '1999 原表只覆盖23个省区市，2000与2001表数和统计对象不同。'}

def query(year, table, keyword=''):
    if isinstance(year, bool) or not isinstance(year, int) or year not in TABLES:
        raise ValueError('year 须为1999、2000或2001')
    if isinstance(table, bool) or not isinstance(table, int) or (not 1 <= table <= len(TABLES[year])):
        raise ValueError('table 不在该年度范围内')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词须为不超过100字的字符串')
    url = f'https://www.moj.gov.cn/pub/sfbgwapp/zwgk/tjxxApp/202105/t20210517_{IDS[year]}.html'
    with requests.get(url, timeout=(10, 25), allow_redirects=True, stream=True) as r:
        r.raise_for_status()
        if any((not h.url.startswith('https://www.moj.gov.cn/') for h in [*r.history, r])):
            raise RuntimeError('跳转离开司法部域名')
        data = []
        size = 0
        for c in r.iter_content(65536):
            size += len(c)
            if size > 3000000:
                raise RuntimeError('响应过大')
            data.append(c)
    s = BeautifulSoup(b''.join(data).decode('utf8'), 'html.parser')
    if f'{year}年全国行政复议' not in s.get_text(' ', strip=True):
        raise RuntimeError('报告年份或标题异常')
    tables = s.find_all('table')
    if len(tables) < len(TABLES[year]):
        raise RuntimeError('表格数量不符')
    rows = []
    for tr in tables[table - 1].find_all('tr'):
        cells = [{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
        if cells:
            rows.append(cells)
    title, expected = TABLES[year][table - 1]
    if len(rows) < 2 or expected not in ''.join(rows[0][0]['text'].split()):
        raise RuntimeError('表格首行不符合预期')
    key = ''.join(keyword.split())
    selected = [row for row in rows if not key or any((key in ''.join(c['text'].split()) for c in row))]
    return {'source': '司法部官网保存的历史统计', 'url': url, 'year': year, 'table': table, 'title': title, 'keyword': keyword, 'total_rows': len(rows), 'matched_rows': len(selected), 'rows': selected, 'note': '1999年原表仅23个省区市，非全国完整总量；年份、表号及申请/受理/审结口径不同。保留跨行跨列及原数字空格，按单元格去空白匹配并返回整行，一行可能包含多个地区。'}
