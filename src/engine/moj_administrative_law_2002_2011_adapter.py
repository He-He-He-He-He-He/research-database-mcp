"""司法部 2002—2011 年全国行政复议、行政应诉历史网页统计表。"""
import release_runtime
import requests
from bs4 import BeautifulSoup
IDS = {2011: 396266, 2010: 396265, 2009: 396264, 2008: 396263, 2007: 396262, 2006: 396261, 2005: 396259, 2004: 396258, 2003: 396256, 2002: 396257}
TITLES = ('省区市收到行政复议申请情况', '国务院部门收到行政复议申请情况', '行政复议申请事项分类情况', '行政复议案件审理情况', '省区市行政应诉案件情况', '国务院部门行政应诉案件情况', '行政应诉案件审理情况')
HEADS = (('省份',), ('部门',), ('事项',), ('审理结果', '处理结果'), ('省份',), ('部门',), ('判决', '已审结', '审理情况'))

def catalog():
    return {'source': '中华人民共和国司法部', 'years': sorted(IDS), 'tables': [{'table': i + 1, 'title': title} for i, title in enumerate(TITLES)], 'note': '仅2002—2011官方网页前7张统计原表，不包含单案。'}

def query(year, table, keyword=''):
    if isinstance(year, bool) or not isinstance(year, int) or year not in IDS:
        raise ValueError('year 须为 2002 至 2011')
    if isinstance(table, bool) or not isinstance(table, int) or (not 1 <= table <= 7):
        raise ValueError('table 须为1至7')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词须为不超过100字的字符串')
    url = 'https://www.moj.gov.cn/pub/sfbgwapp/zwgk/tjxxApp/202105/t20210517_' + str(IDS[year]) + '.html'
    with requests.get(url, timeout=(10, 25), allow_redirects=True, stream=True) as r:
        r.raise_for_status()
        if any((not h.url.startswith('https://www.moj.gov.cn/') for h in [*r.history, r])):
            raise RuntimeError('跳转离开司法部域名')
        chunks = []
        size = 0
        for c in r.iter_content(65536):
            size += len(c)
            if size > 3000000:
                raise RuntimeError('响应过大')
            chunks.append(c)
    s = BeautifulSoup(b''.join(chunks).decode('utf8'), 'html.parser')
    if f'{year}年全国行政复议' not in s.get_text(' ', strip=True):
        raise RuntimeError('年份或标题异常')
    ts = s.find_all('table')
    if len(ts) < 7:
        raise RuntimeError('官方网页表格数量异常')
    rows = []
    for tr in ts[table - 1].find_all('tr'):
        cells = [{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
        if cells:
            rows.append(cells)
    if len(rows) < 2 or not any((head in ''.join(rows[0][0]['text'].split()) for head in HEADS[table - 1])):
        raise RuntimeError('表头异常')
    key = ''.join(keyword.split())
    selected = [row for row in rows if not key or any((key in ''.join(c['text'].split()) for c in row))]
    return {'source': '中华人民共和国司法部，历史数据原发布单位中国政府法制信息网', 'url': url, 'year': year, 'table': table, 'title': TITLES[table - 1], 'keyword': keyword, 'total_rows': len(rows), 'matched_rows': len(selected), 'rows': selected, 'note': '官方历史网页单元格及跨行跨列，按单元格包含匹配后返回整行。单行可含多个省区或部门；申请、受理、结案口径、行政区划和表结构随年变化，请核对原表及原始发布单位。'}
