"""MOF 2008 national, central and local final-account HTML tables."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://yss.mof.gov.cn/caizhengshuju/200907/t20090707_176723.htm'
TITLES = ('2008年全国财政收入决算表', '2008年全国财政支出决算表', '2008年地方财政收入决算表', '2008年地方财政支出决算表', '2008年中央财政收入决算表', '2008年中央财政支出决算表', '2008年中央本级支出决算表', '2008年中央对地方税收返还和转移支付决算表')

def catalog():
    return [{'index': i, 'title': v, 'url': URL} for i, v in enumerate(TITLES)]

def table(index, keyword='', limit=100, offset=0):
    if type(index) is not int or not 0 <= index < len(TITLES):
        raise ValueError('table index must be 0–7')
    if not isinstance(keyword, str) or len(keyword) > 100 or type(limit) is not int or (not 1 <= limit <= 500) or (type(offset) is not int) or (offset < 0):
        raise ValueError('invalid keyword, limit or offset')
    with requests.get(URL, timeout=(10, 40), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        data = bytearray()
        for chunk in r.iter_content(65536):
            data.extend(chunk)
            if len(data) > 3000000:
                raise ValueError('source too large')
    soup = BeautifulSoup(bytes(data), 'html.parser')
    candidate = []
    for t in soup.select('table'):
        trs = [x for x in t.find_all('tr') if x.find_parent('table') is t]
        if len(trs) < 5:
            continue
        head = re.sub('\\s+', '', trs[0].get_text('', strip=True))
        if head == TITLES[index]:
            candidate.append((t, trs))
    if len(candidate) != 1:
        raise ValueError('expected one table matching source title')
    t, trs = candidate[0]
    rows = []
    for n, tr in enumerate(trs, 1):
        cells = [{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
        rows.append({'row': n, 'cells': cells})
    selected = [x for x in rows if keyword in ' '.join((c['text'] for c in x['cells']))]
    return {'source': '财政部2008年全国财政收支决算情况', 'url': URL, 'title': TITLES[index], 'year': 2008, 'total_rows': len(rows), 'matched_rows': len(selected), 'headers': rows[:5], 'offset': offset, 'rows': selected[offset:offset + limit], 'truncated': len(selected) > offset + limit, 'note': '原始单元格与合并属性，预算、调整预算和决算列不同；范围、单位及科目口径须核原表。'}
