"""最高人民法院 2023 年十大知识产权案件简介。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://www.court.gov.cn/zixun/xiangqing/430692.html'

def court_ip_top_cases_2023(query='', timeout=25):
    if not isinstance(query, str) or len(query) > 200:
        raise ValueError('关键词须为不超过 200 字的字符串')
    r = requests.get(URL, timeout=timeout)
    r.raise_for_status()
    x = BeautifulSoup(r.content, 'html.parser').select_one('#zoom')
    if x is None:
        raise ValueError('官方文章正文结构已变更')
    for e in x.select('br'):
        e.replace_with('\n')
    text = x.get_text()
    i = text.find('2023年中国法院10大知识产权案件简介')
    if i < 0:
        raise ValueError('未找到十大案件简介')
    text = text[i:]
    ms = list(re.finditer('(?m)^[ \\t\\u3000]*([一二三四五六七八九十]+)、([^\\n]+)', text))
    if [m.group(1) for m in ms] != list('一二三四五六七八九') + ['十']:
        raise ValueError('案例结构异常')
    rows = []
    for n, m in enumerate(ms, 1):
        block = text[m.end():ms[n].start() if n < len(ms) else len(text)].strip()
        title = m.group(2).strip()
        if '【案情摘要】' not in block or '【典型意义】' not in block:
            raise ValueError('案例正文结构异常')
        if query.strip().casefold() in (title + '\n' + block).casefold():
            rows.append({'case_number': n, 'title': title, 'text': block})
    return {'source': '最高人民法院 2023 年十大知识产权案件简介', 'source_url': URL, 'query': query.strip(), 'matched': len(rows), 'items': rows, 'note': '仅检索官方汇编中 10 件十大案件简介正文，不含同篇另列的 50 件案例目录；摘要非完整裁判文书，需另核对正式裁判及后续状态。'}
