"""司法部全国行政复议统计表（年度网页原表，不含个案）。"""
import release_runtime
import requests
from bs4 import BeautifulSoup
URLS = {2018: 'https://www.moj.gov.cn/pub/sfbgwapp/zwgk/tjxxApp/202105/t20210517_396277.html', 2019: 'https://www.moj.gov.cn/pub/sfbgw/zwxxgk/fdzdgknr/fdzdgknrtjxx/202009/t20200929_392195.html', 2021: 'https://www.moj.gov.cn/pub/sfbgwapp/zwgk/tjxxApp/202305/t20230509_478448.html', 2022: 'https://www.moj.gov.cn/pub/sfbgwapp/zwgk/tjxxApp/202307/t20230711_482423.html', 2023: 'https://www.moj.gov.cn/pub/sfbgwapp/zwgk/tjxxApp/202408/t20240813_504122.html', 2024: 'https://www.moj.gov.cn/pub/sfbgwapp/zwgk/tjxxApp/202507/t20250704_522174.html', 2025: 'https://www.moj.gov.cn/pub/sfbgwapp/zwgk/tjxxApp/202610/t20261009_540454.html'}
URLS[2016] = 'https://www.moj.gov.cn/pub/sfbgwapp/zwgk/tjxxApp/202105/t20210517_396272.html'
TITLES = ('省区市和兵团受理行政复议案件情况', '国务院部门受理行政复议案件情况', '行政复议被申请人情况', '行政复议机关情况', '行政复议案件涉及的领域', '行政复议案件涉及的事项', '行政复议案件审结情况')

def catalog():
    return {'source': '中华人民共和国司法部', 'years': list(URLS), 'tables': [{'table': i + 1, 'title': name} for i, name in enumerate(TITLES)], 'note': '年度报告含行政复议等统计；此入口仅前7张行政复议原表。2016 表1为省区市，不写兵团；具体以各年报告为准。'}

def query(year, table, keyword=''):
    if isinstance(year, bool) or not isinstance(year, int) or year not in URLS:
        raise ValueError('year 支持 2016、2018、2019、2021 至 2025；2017 和 2020 暂未接入')
    if isinstance(table, bool) or not isinstance(table, int) or (not 1 <= table <= 7):
        raise ValueError('table 须为 1 至 7')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('keyword 须不超过100字')
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
    tables = s.find_all('table')
    if len(tables) < 7 or f'{year}年全国行政复议' not in s.get_text(' ', strip=True):
        raise RuntimeError('未识别年度报告表结构')
    rows = []
    for tr in tables[table - 1].find_all('tr'):
        cells = []
        for c in tr.find_all(['td', 'th'], recursive=False):
            cells.append({'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))})
        if cells:
            rows.append(cells)
    if len(rows) < 2:
        raise RuntimeError('官方表为空或结构异常')
    first = ''.join(rows[0][0]['text'].split())
    expected = ('省份', '部门', '被申请人', '复议机关', '领域', '事项', '审理结果')[table - 1]
    if expected not in first:
        raise RuntimeError('官方表顺序或表头发生变化')
    selected = [row for row in rows if not keyword or any((keyword.casefold() in x['text'].casefold() for x in row))]
    title = '省区市受理行政复议案件情况' if year == 2016 and table == 1 else TITLES[table - 1]
    return {'source': '中华人民共和国司法部', 'url': url, 'year': year, 'table': table, 'title': title, 'keyword': keyword, 'total_rows': len(rows), 'matched_rows': len(selected), 'rows': selected, 'note': '网页原表按行返回，保留跨行跨列；同一行可能有多个省区或部门，筛选后返回整行。统计口径、表头与年份差异须按原文核对；非个案及裁判文书。'}
