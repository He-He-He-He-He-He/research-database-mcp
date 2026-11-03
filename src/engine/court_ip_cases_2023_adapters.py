"""最高人民法院 2023 年十大案件与 50 件典型知识产权案例目录。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://www.court.gov.cn/zixun/xiangqing/430692.html'

def court_ip_cases_2023(query='', group='all', timeout=25):
    if not isinstance(query, str) or len(query) > 200:
        raise ValueError('关键词须为不超过 200 字的字符串')
    if group not in ('all', 'top', 'typical'):
        raise ValueError('group 须为 all、top 或 typical')
    r = requests.get(URL, timeout=timeout)
    r.raise_for_status()
    x = BeautifulSoup(r.content, 'html.parser').select_one('#zoom')
    if x is None:
        raise ValueError('官方文章正文结构已变更')
    for e in x.select('br'):
        e.replace_with('\n')
    text = x.get_text()
    a = text.index('2023年中国法院10大知识产权案件')
    b = text.index('2023年中国法院50件典型知识产权案例', a)
    c = text.index('2023年中国法院10大知识产权案件简介', b)
    top = [line.strip() for line in text[a:b].splitlines() if re.match('^[ \\u3000]*[一二三四五六七八九十]+、', line)]
    lines = [line.strip() for line in text[b:c].splitlines() if line.strip()]
    typ = []
    category = ''
    sub = ''
    for line in lines:
        if re.match('^[一二三]、知识产权', line):
            category = line
            sub = ''
        elif re.match('^（[一二三四五六七八九十]+）', line):
            sub = line
        else:
            m = re.match('^(\\d+)\\.(.+)', line)
            if m:
                typ.append({'group': 'typical', 'category': category, 'subcategory': sub, 'list_number': int(m.group(1)), 'entry': m.group(2)})
    if len(top) != 10 or len(typ) != 50:
        raise ValueError('官方案例目录结构异常')
    items = [{'group': 'top', 'entry': line} for line in top] + typ
    items = [x for x in items if (group == 'all' or x['group'] == group) and query.strip().casefold() in x['entry'].casefold()]
    return {'source': '最高人民法院 2023 年十大知识产权案件及 50 件典型案例目录', 'source_url': URL, 'group': group, 'query': query.strip(), 'matched': len(items), 'items': items, 'note': '仅检索原文中 10+50 个目录条目的标题及案号，不检索案例摘要或完整裁判文书；同一案件分组不表示互不重复。应核对正式裁判及后续状态。'}
