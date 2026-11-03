"""人社部、最高法院第二、第三批劳动争议典型案例。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
SOURCES = {2: ('https://www.court.gov.cn/zixun/xiangqing/319151.html', '2021-08-26', 10), 3: ('https://www.court.gov.cn/zixun/xiangqing/401172.html', '2023-05-26', 6)}

def court_labor_disputes_batch2_3(query='', batch=2, timeout=25):
    if not isinstance(query, str) or len(query) > 200:
        raise ValueError('关键词须为不超过 200 字的字符串')
    if isinstance(batch, bool) or batch not in SOURCES:
        raise ValueError('批次须为 2 或 3')
    url, date, count = SOURCES[batch]
    r = requests.get(url, timeout=timeout)
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
    if batch == 2:
        ms = list(re.finditer('(?m)^[ \\t\\u3000]*案例\\s*(\\d+)[.．、:： ]+([^\\n]+)$', text))
        if [int(m.group(1)) for m in ms] != list(range(1, 11)) * 2:
            raise ValueError('案例目录或正文分段异常')
        ms = ms[10:]
    else:
        ms = list(re.finditer('(?m)^[ \\t\\u3000]*案例\\s*(\\d+)\\.[ \\t\\u3000]*$', text))
        if [int(m.group(1)) for m in ms] != list(range(1, 7)):
            raise ValueError('案例正文分段异常')
    rows = []
    for n, m in enumerate(ms, 1):
        block = text[m.end():ms[n].start() if n < len(ms) else len(text)].strip()
        lines = [v.strip() for v in block.splitlines() if v.strip()]
        title = m.group(2).strip() if batch == 2 else lines[0] if lines else ''
        if '基本案情' not in block or '典型意义' not in block:
            raise ValueError('案例正文结构异常')
        if query.strip().casefold() in (title + '\n' + block).casefold():
            rows.append({'case_number': n, 'title': title, 'text': block})
    return {'source': f'人社部与最高人民法院第 {batch} 批劳动人事争议典型案例', 'source_url': url, 'publication_date': date, 'batch': batch, 'query': query.strip(), 'matched': len(rows), 'items': rows, 'note': f'仅搜索此篇通报的 {count} 件案例正文，不是全部劳动争议或完整裁判文书；具体裁判及后续状态须另核对。'}
