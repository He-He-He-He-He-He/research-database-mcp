"""2007 first national pollution source census bulletin and HTML tables."""
import release_runtime
import requests
from bs4 import BeautifulSoup
SOURCES = {1: 'https://www.stats.gov.cn/sj/tjgb/qttjgb/qgqttjgb/202302/t20230218_1913282.html'}
TITLES = {1: '第一次全国污染源普查公报'}

def catalog():
    return [{'part': y, 'scope': TITLES[y], 'url': u} for y, u in SOURCES.items()]

def table(part, keyword='', limit=100, offset=0):
    if type(part) is not int or part not in SOURCES:
        raise ValueError('part must be 1')
    if not isinstance(keyword, str) or len(keyword) > 100 or type(limit) is not int or (not 1 <= limit <= 500) or (type(offset) is not int) or (offset < 0):
        raise ValueError('invalid keyword, limit or offset')
    u = SOURCES[part]
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
    return {'part': part, 'scope': TITLES[part], 'year': 2007, 'url': u, 'source': '第一次全国污染源普查公报', 'tables': tables, 'note': '地区表所列为普查对象数量，不是污染物排放量；与后次普查比较须核对范围与口径。其他正文内容不在表格接口内。表头、脚注和范围见原文；重复表格按完全一致去重。'}
