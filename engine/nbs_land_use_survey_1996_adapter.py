"""First agriculture census land-use survey: official bulletin tables."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://www.stats.gov.cn/sj/tjgb/nypcgb/qgnypcgb/202302/t20230206_1902090.html'

def tables(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    with requests.get(URL, timeout=(10, 45), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        data = bytearray()
        for chunk in r.iter_content(65536):
            data.extend(chunk)
            if len(data) > 5000000:
                raise ValueError('document too large')
    soup = BeautifulSoup(bytes(data), 'html.parser')
    found = {}
    for t in soup.find_all('table'):
        if t.find('table'):
            continue
        cap = next((p.get_text(' ', strip=True) for p in t.find_all_previous('p', limit=8) if re.match('^表\\s*[123]\\s', p.get_text(' ', strip=True))), '')
        m = re.match('^表\\s*([123])', cap)
        if not m:
            continue
        n = int(m.group(1))
        rows = []
        for tr in t.find_all('tr'):
            if tr.find_parent('table') is not t:
                continue
            rows.append([{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)])
        item = {'number': n, 'caption': cap, 'rows': rows}
        if n in found and found[n] != item:
            raise ValueError('conflicting duplicated table')
        found[n] = item
    if set(found) != {1, 2, 3}:
        raise ValueError('expected three official data tables')
    result = []
    q = ''.join(keyword.split())
    for n in (1, 2, 3):
        item = found[n]
        rows = item['rows']
        result.append({'number': n, 'caption': item['caption'], 'header': rows[:2], 'matched_rows': [{'row': i, 'cells': r} for i, r in enumerate(rows, 1) if q in ''.join((''.join(c['text'].split()) for c in r))]})
    return {'source': '国家统计局 第一次全国农业普查 土地利用现状调查主要数据成果公报', 'url': URL, 'tables': result, 'note': '按原表行与单元格返回，三张表分属耕地分布、25度以上坡耕地和灌溉设施占比，须按表标题与单位解释。原文关于中部地区的比例正文为 4.32%，表中为 43.2%，存在冲突，未擅自修订。'}
