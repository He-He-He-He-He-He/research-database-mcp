"""2018–20 NRTA broadcast and network audiovisual annual statistical bulletins."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
SOURCES = {2018: 'https://www.nrta.gov.cn/art/2019/4/23/art_113_42604.html', 2019: 'https://www.nrta.gov.cn/art/2020/7/8/art_113_52026.html', 2020: 'https://www.nrta.gov.cn/art/2021/4/19/art_2555_55908.html'}

def bulletin(year, keyword=''):
    if type(year) is not int or year not in SOURCES:
        raise ValueError('year must be 2018–2020')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    url = SOURCES[year]
    with requests.get(url, timeout=(10, 45), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        data = bytearray()
        for chunk in r.iter_content(65536):
            data.extend(chunk)
            if len(data) > 5000000:
                raise ValueError('document too large')
    soup = BeautifulSoup(bytes(data), 'html.parser')
    root = soup.select_one('#zoom')
    if not root:
        raise ValueError('bulletin content missing')
    paragraphs = [' '.join(p.get_text(' ', strip=True).split()) for p in root.select('p') if not p.find('p')]
    paragraphs = [p for p in paragraphs if p]
    if len(paragraphs) < 10 or not any((str(year) + '年全国广播电视' in ''.join(p.split()) for p in paragraphs)):
        raise ValueError('unexpected bulletin body')
    q = ''.join(keyword.split())
    notes = [x for x in paragraphs if re.match('^(?:\\[[ivxIVX\\d]+\\]|[1-9](?=\\s|[\\u4e00-\\u9fff]))', x)]
    return {'year': year, 'url': url, 'source': '国家广播电视总局全国广播电视行业统计公报', 'paragraphs': [{'number': i, 'text': p} for i, p in enumerate(paragraphs, 1) if q in ''.join(p.split())], 'footnotes': notes, 'note': '正文原样返回，收入和用户数据各有统计范围，年度口径变化不能不加核实拼接；2018年服务业总收入的构成不一定与财政补助和实际创收简单相加，应参照脚注。'}

def revenue(year):
    r = bulletin(year, '全国广播电视')
    items = []
    for p in r['paragraphs']:
        text = ''.join(p['text'].split())
        m = re.search(f'{year}年全国广播电视(?:服务业|行业)总收入([0-9.]+)亿元，.*?同比增长([0-9.]+)%', text)
        if m:
            items.append({'indicator': '全国广播电视服务业总收入' if year == 2018 else '全国广播电视行业总收入', 'value': m.group(1), 'unit': '亿元', 'growth_percent': m.group(2), 'source_paragraph': p['text']})
    if len(items) != 1:
        raise ValueError('expected one unique revenue paragraph')
    return {'year': year, 'url': r['url'], 'source': r['source'], 'items': items, 'footnotes': r['footnotes'], 'note': r['note']}
