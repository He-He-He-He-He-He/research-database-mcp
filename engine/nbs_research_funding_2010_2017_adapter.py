"""2010–2017 official national R&D expenditure bulletins and HTML tables."""
import release_runtime
import requests
from bs4 import BeautifulSoup
SOURCES = {2010: 'https://www.mof.gov.cn/gkml/bulinggonggao/tongzhitonggao/201109/t20110928_597044.htm', 2011: 'https://www.mof.gov.cn/zhengwuxinxi/caizhengxinwen/201210/t20121025_690008.htm', 2012: 'https://m.mof.gov.cn/czsj/201309/t20130926_993359.htm', 2013: 'https://www.stats.gov.cn/sj/tjgb/rdpcgb/qgkjjftrtjgb/202302/t20230206_1902123.html', 2014: 'https://www.mof.gov.cn/gkml/caizhengshuju/201511/t20151127_1586024.htm', 2015: 'https://www.stats.gov.cn/sj/zxfb/202302/t20230203_1899323.html', 2016: 'https://www.stats.gov.cn/sj/tjgb/rdpcgb/qgkjjftrtjgb/202302/t20230206_1902126.html', 2017: 'https://www.stats.gov.cn/sj/tjgb/rdpcgb/qgkjjftrtjgb/202302/t20230206_1902127.html'}

def catalog():
    return [{'year': y, 'url': u} for y, u in SOURCES.items()]

def table(year, keyword='', limit=100, offset=0):
    if type(year) is not int or year not in SOURCES:
        raise ValueError('year must be 2010–2017')
    if not isinstance(keyword, str) or len(keyword) > 100 or type(limit) is not int or (not 1 <= limit <= 500) or (type(offset) is not int) or (offset < 0):
        raise ValueError('invalid keyword, limit or offset')
    u = SOURCES[year]
    with requests.get(u, timeout=(10, 45), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        data = bytearray()
        for chunk in r.iter_content(65536):
            data.extend(chunk)
            if len(data) > 5000000:
                raise ValueError('document too large')
    soup = BeautifulSoup(bytes(data), 'html.parser')
    tables = []
    allrows = []
    for t in soup.select('table'):
        if t.find('table') or len(t.select('tr')) < 4:
            continue
        rows = []
        for n, tr in enumerate(t.find_all('tr'), 1):
            if tr.find_parent('table') is not t:
                continue
            cells = [{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
            rows.append({'row': n, 'cells': cells})
        if rows in allrows:
            continue
        allrows.append(rows)
        q = ''.join(keyword.split())
        selected = [x for x in rows if q in ''.join((''.join(c['text'].split()) for c in x['cells']))]
        tables.append({'total_rows': len(rows), 'matched_rows': len(selected), 'headers': rows[:4], 'offset': offset, 'rows': selected[offset:offset + limit], 'truncated': len(selected) > offset + limit})
    if not tables:
        raise ValueError('no HTML tables found; source may be unavailable or protected')
    return {'year': year, 'url': u, 'source': '国家统计局、科技部、财政部全国科技经费投入统计公报', 'tables': tables, 'note': '原版公报数据可能被后续修订；表头、脚注和调查范围见原文。重复的移动端/桌面端表格按完全一致去重。'}
