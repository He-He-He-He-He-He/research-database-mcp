"""MOF 2010–2012 central and local public finance final accounts HTML tables."""
import release_runtime
import requests
from bs4 import BeautifulSoup
SOURCES = {2010: {'central_revenue': 'https://yss.mof.gov.cn/2010juesuan/201107/t20110720_578447.htm', 'local_revenue': 'https://yss.mof.gov.cn/2010juesuan/201107/t20110720_578445.htm', 'central_expenditure': 'https://yss.mof.gov.cn/2010juesuan/201107/t20110720_578437.htm', 'local_expenditure': 'https://yss.mof.gov.cn/2010juesuan/201107/t20110720_578420.htm'}, 2011: {'central_revenue': 'https://yss.mof.gov.cn/2011qgczjs/201207/t20120710_665249.htm', 'local_revenue': 'https://yss.mof.gov.cn/2011qgczjs/201207/t20120710_665251.htm', 'central_expenditure': 'https://yss.mof.gov.cn/2011qgczjs/201207/t20120710_665279.htm', 'local_expenditure': 'https://yss.mof.gov.cn/2011qgczjs/201207/t20120710_665276.htm'}, 2012: {'central_revenue': 'https://yss.mof.gov.cn/2012qhczjs/201307/t20130715_966215.htm', 'local_revenue': 'https://yss.mof.gov.cn/2012qhczjs/201307/t20130715_966217.htm', 'central_expenditure': 'https://yss.mof.gov.cn/2012qhczjs/201307/t20130715_966187.htm', 'local_expenditure': 'https://yss.mof.gov.cn/2012qhczjs/201307/t20130715_966263.htm'}}

def catalog():
    return [{'year': year, 'kind': kind, 'url': url} for year, d in sorted(SOURCES.items()) for kind, url in d.items()]

def table(year, kind, keyword='', limit=100, offset=0):
    if type(year) is not int or year not in SOURCES or kind not in ('central_revenue', 'local_revenue', 'central_expenditure', 'local_expenditure'):
        raise ValueError('year 2010–2012; select central/local revenue/expenditure')
    if not isinstance(keyword, str) or len(keyword) > 100 or type(limit) is not int or (not 1 <= limit <= 500) or (type(offset) is not int) or (offset < 0):
        raise ValueError('invalid keyword, limit or offset')
    url = SOURCES[year][kind]
    with requests.get(url, timeout=(10, 45), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        buf = bytearray()
        for part in r.iter_content(65536):
            buf.extend(part)
            if len(buf) > 5000000:
                raise ValueError('document too large')
    soup = BeautifulSoup(bytes(buf), 'html.parser')
    tables = [t for t in soup.select('table') if len(t.find_all('tr')) > 10]
    if len(tables) != 1:
        raise ValueError('expected one official table')
    rows = []
    for n, tr in enumerate(tables[0].find_all('tr'), 1):
        if tr.find_parent('table') is not tables[0]:
            continue
        row = [{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
        rows.append({'row': n, 'cells': row})
    filtered = [x for x in rows if keyword in ' '.join((c['text'] for c in x['cells']))]
    return {'source': '财政部中央及地方公共财政决算', 'year': year, 'kind': kind, 'url': url, 'total_rows': len(rows), 'matched_rows': len(filtered), 'headers': rows[:5], 'offset': offset, 'rows': filtered[offset:offset + limit], 'truncated': len(filtered) > offset + limit, 'note': '原始表格及合并属性；单位为亿元，预算、决算及百分比是不同列。科目和统计口径随年调整，空白不能当作零。'}
