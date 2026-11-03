"""最高法院等四部门金融消费者与投资者保护典型案例。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://www.court.gov.cn/zixun/xiangqing/513941.html'

def court_financial_consumer_2026(query='', timeout=25):
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
    matches = list(re.finditer('(?m)^[ \\t\\u3000]*案例\\s*([一二三四五六])[、.．:： ]+([^\\n]+)$', text))
    if [m.group(1) for m in matches] != list('一二三四五六') * 2:
        raise ValueError('案例目录或正文分段异常')
    ms = matches[6:]
    rows = []
    for n, m in enumerate(ms, 1):
        block = text[m.end():ms[n].start() if n < len(ms) else len(text)].strip()
        title = m.group(2).strip()
        if '【基本案情】' not in block or '【典型意义】' not in block:
            raise ValueError('案例正文结构异常')
        if query.strip().casefold() in (title + '\n' + block).casefold():
            rows.append({'case_number': n, 'title': title, 'text': block})
    return {'source': '最高人民法院等四部门金融消费者、投资者合法权益保护典型案例', 'source_url': URL, 'publication_date': '2026-10-12', 'query': query.strip(), 'matched': len(rows), 'items': rows, 'note': '仅搜索此篇通报的 6 件案例，含裁判或调解内容，不是全部金融纠纷或完整裁判文书；具体裁判及后续状态须另核对。'}
