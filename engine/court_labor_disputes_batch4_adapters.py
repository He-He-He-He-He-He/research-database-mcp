"""最高人民法院 第四批劳动人事争议典型案例官方汇编。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://www.court.gov.cn/zixun/xiangqing/462311.html'

def court_labor_disputes_batch4(query='', timeout=25):
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
    all_markers = list(re.finditer('(?m)^[ \\t\\u3000]*案例\\s*(\\d+)\\.(.+)$', text))
    if [int(m.group(1)) for m in all_markers] != list(range(1, 6)) * 2:
        raise ValueError('案例分段结构异常')
    markers = all_markers[5:]
    rows = []
    for i, m in enumerate(markers):
        block = text[m.end():markers[i + 1].start() if i + 1 < len(markers) else len(text)].strip()
        if '基本案情' not in block:
            raise ValueError('案例正文结构异常')
        title = m.group(2).strip()
        if query.strip().casefold() in (title + '\n' + block).casefold():
            rows.append({'case_number': int(m.group(1)), 'title': title, 'text': block})
    return {'source': '人社部与最高人民法院第四批劳动人事争议典型案例', 'source_url': URL, 'publication_date': '2025-04-16', 'query': query.strip(), 'matched': len(rows), 'items': rows, 'note': '仅对这一篇官方发布的 5 件典型案例做正文包含匹配，不是全部劳动争议或完整裁判文书；需另核对实际裁判和后续状态。'}
