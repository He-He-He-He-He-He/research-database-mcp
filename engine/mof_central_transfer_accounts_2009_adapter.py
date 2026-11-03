"""Ministry of Finance 2009 central level expenditures and intergovernmental transfer final accounts."""
import release_runtime
import requests
from bs4 import BeautifulSoup
SOURCES = {'central_level_expenditure': ('2009年中央本级支出决算表', 'https://yss.mof.gov.cn/2009nianquanguojuesuan/201007/t20100709_327126.htm'), 'transfers': ('2009年中央对地方税收返还和转移支付决算表', 'https://yss.mof.gov.cn/2009nianquanguojuesuan/201007/t20100709_327125.htm')}

def catalog():
    return [{'year': 2009, 'kind': k, 'title': v[0], 'url': v[1]} for k, v in SOURCES.items()]

def table(kind, keyword='', limit=100, offset=0):
    if kind not in SOURCES:
        raise ValueError('unknown table kind')
    if not isinstance(keyword, str) or len(keyword) > 100 or type(limit) is not int or (not 1 <= limit <= 500) or (type(offset) is not int) or (offset < 0):
        raise ValueError('invalid keyword, limit or offset')
    title, url = SOURCES[kind]
    with requests.get(url, timeout=(10, 45), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        data = bytearray()
        for chunk in r.iter_content(65536):
            data.extend(chunk)
            if len(data) > 5000000:
                raise ValueError('document too large')
    soup = BeautifulSoup(bytes(data), 'html.parser')
    tables = [t for t in soup.select('table') if len(t.find_all('tr')) > 10]
    if len(tables) != 1:
        raise ValueError('expected one official data table')
    rows = []
    for n, tr in enumerate(tables[0].find_all('tr'), 1):
        if tr.find_parent('table') is not tables[0]:
            continue
        cells = [{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
        rows.append({'row': n, 'cells': cells})
    selected = [row for row in rows if keyword in ' '.join((c['text'] for c in row['cells']))]
    return {'source': '财政部预算司', 'year': 2009, 'title': title, 'kind': kind, 'url': url, 'total_rows': len(rows), 'matched_rows': len(selected), 'headers': rows[:5], 'offset': offset, 'rows': selected[offset:offset + limit], 'truncated': len(selected) > offset + limit, 'note': '单位亿元；中央本级支出与对地方税收返还和转移支付范围不同；预算数、决算数及占比为不同列。空白不等于零。'}
