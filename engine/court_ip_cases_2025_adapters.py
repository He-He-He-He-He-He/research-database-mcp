"""最高人民法院 2025 年知识产权典型案例官方汇编。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://www.court.gov.cn/zixun/xiangqing/497941.html'

def court_ip_cases_2025(query='', timeout=25):
    if not isinstance(query, str) or len(query) > 200:
        raise ValueError('关键词须为不超过 200 字的字符串')
    r = requests.get(URL, timeout=timeout)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    x = s.select_one('#zoom')
    if x is None:
        raise ValueError('官方文章正文结构已变更')
    for e in x.select('br'):
        e.replace_with('\n')
    for e in x.select('p'):
        e.insert_before('\n')
        e.insert_after('\n')
    text = x.get_text()
    markers = list(re.finditer('(?m)^[\\s\\u3000]*案例\\s*(\\d+)[\\s\\u3000]*$', text))
    if [int(m.group(1)) for m in markers] != list(range(1, 11)):
        raise ValueError('案例分段结构异常')
    rows = []
    for i, m in enumerate(markers):
        block = text[m.end():markers[i + 1].start() if i + 1 < len(markers) else len(text)].strip()
        lines = [z.strip() for z in block.splitlines() if z.strip()]
        if len(lines) < 3 or '【基本案情】' not in block:
            raise ValueError('案例正文结构异常')
        if query.strip().casefold() in block.casefold():
            rows.append({'case_number': int(m.group(1)), 'title': lines[0], 'court_case_identifier': lines[1], 'text': block})
    return {'source': '最高人民法院 2025 年人民法院知识产权典型案例', 'source_url': URL, 'publication_date': '2026-04-20', 'query': query.strip(), 'matched': len(rows), 'items': rows, 'note': '仅对这一篇官方发布的 10 件典型案例做正文包含匹配；不是法院全部判决或全量案例库。正文为案例通报而非完整裁判文书，需另核对实际裁判和后续状态。'}
