"""最高人民法院平台经营和消费者权益五件典型案例通报。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://www.court.gov.cn/zixun/xiangqing/507691.html'

def court_platform_cases_2026(query='', timeout=25):
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
    ms = list(re.finditer('(?m)^[ \\t\\u3000]*案例([一二三四五])[ \\t\\u3000]*$', text))
    if [m.group(1) for m in ms] != list('一二三四五'):
        raise ValueError('案例结构异常')
    rows = []
    for n, m in enumerate(ms, 1):
        block = text[m.end():ms[n].start() if n < len(ms) else len(text)].strip()
        lines = [z.strip() for z in block.splitlines() if z.strip()]
        if len(lines) < 2 or '【案例摘要】' not in block or '【典型意义】' not in block:
            raise ValueError('案例正文结构异常')
        if query.strip().casefold() in block.casefold():
            rows.append({'case_number': n, 'title': lines[0], 'text': block})
    return {'source': '最高人民法院依法规范平台经营、保护消费者合法权益典型案例', 'source_url': URL, 'publication_date': '2026-08-03', 'query': query.strip(), 'matched': len(rows), 'items': rows, 'note': '仅检索本篇公开通报中的 5 件案例，不是全量平台经营案件或完整裁判文书；具体裁判及后续状态须另核对。'}
