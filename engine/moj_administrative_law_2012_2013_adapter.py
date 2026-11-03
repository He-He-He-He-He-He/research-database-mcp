"""司法部 2012、2013 年全国行政复议和应诉历史统计表。"""
import release_runtime
import requests
from bs4 import BeautifulSoup
URLS = {2012: 'https://www.moj.gov.cn/pub/sfbgw/zwxxgk/fdzdgknr/fdzdgknrtjxx/201402/t20140225_350038.html', 2013: 'https://www.moj.gov.cn/pub/sfbgw/zwxxgk/fdzdgknr/fdzdgknrtjxx/201403/t20140324_350040.html'}
TITLES = ('省区市收到行政复议申请情况', '国务院部门收到行政复议申请情况', '行政复议申请事项分类情况', '行政复议案件审理情况', '省区市行政应诉案件情况', '国务院部门行政应诉案件情况', '行政应诉案件审理情况')

def catalog():
    return {'source': '中华人民共和国司法部', 'years': list(URLS), 'tables': [{'table': i + 1, 'title': x} for i, x in enumerate(TITLES)], 'note': '仅2012及2013年度网页中7张历史统计原表，不含个案。'}

def query(year, table, keyword=''):
    if isinstance(year, bool) or not isinstance(year, int) or year not in URLS:
        raise ValueError('year 须为 2012 或 2013')
    if isinstance(table, bool) or not isinstance(table, int) or (not 1 <= table <= 7):
        raise ValueError('table 须为1至7')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词须为不超过100字的字符串')
    url = URLS[year]
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
    ts = s.find_all('table')
    if len(ts) != 7:
        raise RuntimeError('表格数量不符，可能网站改版')
    rows = []
    for tr in ts[table - 1].find_all('tr'):
        cells = [{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
        if cells:
            rows.append(cells)
    if len(rows) < 2 or ('省份', '部门', '事项', '审理结果', '省份', '部门', '判决')[table - 1] not in ''.join(rows[0][0]['text'].split()):
        raise RuntimeError('表格首行不符合预期')
    selected = [row for row in rows if not keyword or any((keyword in c['text'] for c in row))]
    return {'source': '中华人民共和国司法部', 'url': url, 'year': year, 'table': table, 'title': TITLES[table - 1], 'keyword': keyword, 'total_rows': len(rows), 'matched_rows': len(selected), 'rows': selected, 'note': '网页原表单元格和跨行跨列，含历史分类及合计；关键词命中时返回整行，一行可包含多个省区或部门。各年统计范围及与后续年度口径须核原表；不含个案。'}
