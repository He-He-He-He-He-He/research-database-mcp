"""最高人民法院新就业形态劳动者权益保障典型案例。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://www.court.gov.cn/zixun/xiangqing/463871.html'

def court_gig_workers_2025(query='', timeout=25):
    if not isinstance(query, str) or len(query) > 200:
        raise ValueError('关键词须为不超过 200 字的字符串')
    r = requests.get(URL, timeout=timeout)
    r.raise_for_status()
    x = BeautifulSoup(r.content, 'html.parser').select_one('#zoom')
    if x is None:
        raise ValueError('官方文章正文结构已变更')
    for e in x.select('br'):
        e.replace_with('\n')
    for e in x.select('p'):
        e.insert_before('\n')
        e.insert_after('\n')
    text = x.get_text()
    matches = list(re.finditer('(?m)^[ \\t\\u3000]*案例\\s*(\\d+)[ \\t\\u3000]*(.+)$', text))
    if [m.group(1) for m in matches] != list('1234') * 2:
        raise ValueError('案例分段结构异常')
    ms = matches[4:]
    rows = []
    for n, m in enumerate(ms, 1):
        block = text[m.end():ms[n].start() if n < len(ms) else len(text)].strip()
        title = m.group(2).strip()
        if '基本案情' not in block or '裁判结果及理由' not in block:
            raise ValueError('案例正文结构异常')
        if query.strip().casefold() in (title + '\n' + block).casefold():
            rows.append({'case_number': n, 'title': title, 'text': block})
    return {'source': '最高人民法院新就业形态劳动者权益保障典型案例', 'source_url': URL, 'publication_date': '2025-04-30', 'query': query.strip(), 'matched': len(rows), 'items': rows, 'note': '仅搜索此篇公开通报的 4 件案例，不是所有劳动争议，也不是完整裁判文书；具体裁判及后续状态须另核对。'}
