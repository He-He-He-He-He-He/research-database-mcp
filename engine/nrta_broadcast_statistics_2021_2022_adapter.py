"""2021–22 NRTA broadcast and network audiovisual annual statistical bulletins."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
SOURCES = {2021: 'https://www.nrta.gov.cn/art/2022/4/25/art_113_60195.html', 2022: 'https://www.nrta.gov.cn/art/2023/4/27/art_113_64140.html'}

def bulletin(year, keyword=''):
    if type(year) is not int or year not in SOURCES:
        raise ValueError('year must be 2021 or 2022')
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
    if len(paragraphs) < 10 or not any((str(year) + '年全国广播电视行业总收入' in ''.join(p.split()) for p in paragraphs)):
        raise ValueError('unexpected bulletin body')
    q = ''.join(keyword.split())
    notes = [x for x in paragraphs if re.match('^(?:\\[\\d+\\]|\\d+\\s)', x)]
    return {'year': year, 'url': url, 'source': '国家广播电视总局全国广播电视行业统计公报', 'paragraphs': [{'number': i, 'text': p} for i, p in enumerate(paragraphs, 1) if q in ''.join(p.split())], 'footnotes': notes, 'note': '正文原样返回，收入和用户数据各有统计范围，年度口径变化不能不加核实拼接；2022年OTT为平均月度活跃用户，2021年为用户数。'}

def revenue(year):
    r = bulletin(year, '全国广播电视行业总收入')
    items = []
    for p in r['paragraphs']:
        text = ''.join(p['text'].split())
        m = re.search(f'{year}年全国广播电视行业总收入([0-9.]+)亿元，同比增长([0-9.]+)%', text)
        if m:
            items.append({'indicator': '全国广播电视行业总收入', 'value': m.group(1), 'unit': '亿元', 'growth_percent': m.group(2), 'source_paragraph': p['text']})
    if len(items) != 1:
        raise ValueError('expected one unique revenue paragraph')
    return {'year': year, 'url': r['url'], 'source': r['source'], 'items': items, 'footnotes': r['footnotes'], 'note': r['note']}
