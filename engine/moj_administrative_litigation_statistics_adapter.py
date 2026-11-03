"""司法部全国行政应诉年度统计网页原表。"""
import release_runtime
import requests
from bs4 import BeautifulSoup
from moj_administrative_reconsideration_statistics_adapter import URLS
TABLES = {2022: {8: ('省区市和兵团行政应诉案件情况', (7,), '省份'), 9: ('国务院部门行政应诉案件情况', (8,), '部门'), 10: ('行政应诉案件被告情况', (9,), '被告'), 11: ('行政应诉案件涉及的领域', (10,), '领域'), 12: ('行政应诉案件涉及的事项', (11,), '事项'), 13: ('行政应诉案件审理情况', (12, 13), '一审判决')}, 2023: {8: ('省区市和兵团行政应诉案件情况', (7,), '省份'), 9: ('国务院部门行政应诉案件情况', (8,), '部门'), 10: ('行政应诉案件被告情况', (9,), '被告'), 11: ('行政应诉案件审理情况', (10, 11), '一审判决')}}
for _year in (2018, 2019, 2021):
    TABLES[_year] = TABLES[2022].copy()
TABLES[2016] = {8: ('省区市行政应诉案件情况', (7,), '省份'), 9: ('国务院部门行政应诉案件情况', (8,), '部门'), 10: ('行政应诉案件被告情况', (9,), '被告'), 11: ('行政应诉案件涉及的领域', (10,), '领域'), 12: ('行政应诉案件审理情况', (11, 12), '一审判决')}

def catalog():
    return {'source': '中华人民共和国司法部', 'years': {str(y): [{'table': k, 'title': v[0], 'segments': len(v[1])} for k, v in d.items()] for y, d in sorted(TABLES.items())}, 'note': '仅已列明年份的官方行政应诉表；不代表其他年度不存在。'}

def query(year, table, keyword=''):
    if isinstance(year, bool) or not isinstance(year, int) or year not in TABLES:
        raise ValueError('year 须为 2016、2018、2019、2021、2022 或 2023')
    if isinstance(table, bool) or not isinstance(table, int) or table not in TABLES[year]:
        raise ValueError('该年度没有接入所选表')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('keyword 须为不超过100字的字符串')
    title, indices, first = TABLES[year][table]
    url = URLS[year]
    with requests.get(url, timeout=(10, 20), stream=True, allow_redirects=True) as r:
        r.raise_for_status()
        if any((not h.url.startswith('https://www.moj.gov.cn/') for h in [*r.history, r])):
            raise RuntimeError('跳转离开司法部域名')
        chunks = []
        size = 0
        for chunk in r.iter_content(65536):
            size += len(chunk)
            if size > 3000000:
                raise RuntimeError('页面超过大小上限')
            chunks.append(chunk)
    s = BeautifulSoup(b''.join(chunks).decode('utf-8'), 'html.parser')
    if f'{year}年全国行政复议' not in s.get_text(' ', strip=True):
        raise RuntimeError('未识别年度报告')
    tables = s.find_all('table')
    if max(indices) >= len(tables):
        raise RuntimeError('网页表格数量异常')
    segments = []
    for index in indices:
        rows = []
        for tr in tables[index].find_all('tr'):
            cells = [{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
            if cells:
                rows.append(cells)
        if len(rows) < 2:
            raise RuntimeError('官方表格为空或结构异常')
        if first not in ''.join(rows[0][0]['text'].split()):
            raise RuntimeError('表序或表头改变')
        selected = [row for row in rows if not keyword or any((keyword.casefold() in c['text'].casefold() for c in row))]
        segments.append({'source_table_index': index + 1, 'total_rows': len(rows), 'matched_rows': len(selected), 'rows': selected})
    return {'source': '中华人民共和国司法部', 'url': url, 'year': year, 'table': table, 'title': title, 'segments': segments, 'note': '年度网页行政应诉统计原表；保留每一段表格及跨行跨列，不自动合并表头；筛选按整行返回，单行可能含多个省份或部门。与行政复议统计、案件个人信息和裁判文书不同。'}
