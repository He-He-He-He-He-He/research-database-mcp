"""2018–2022 official national R&D expenditure bulletins and HTML tables."""
import release_runtime
import requests
from bs4 import BeautifulSoup
SOURCES = {2018: 'https://www.most.gov.cn/kjbgz/201909/t20190903_148573.html', 2019: 'https://m.mof.gov.cn/czxw/202008/t20200831_3578026.htm', 2020: 'https://www.stats.gov.cn/sj/zxfb/202302/t20230203_1901227.html', 2021: 'https://www.stats.gov.cn/sj/zxfb/202302/t20230203_1901565.html', 2022: 'https://www.most.gov.cn/xxgk/xinxifenlei/fdzdgknr/kjtjbg/kjtj2023/202410/t20241015_192156.html'}

def catalog():
    return [{'year': y, 'url': u} for y, u in SOURCES.items()]

def table(year, keyword='', limit=100, offset=0):
    if type(year) is not int or year not in SOURCES:
        raise ValueError('year must be 2018–2022')
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
