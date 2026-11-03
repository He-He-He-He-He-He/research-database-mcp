"""江苏消防救援总队网站转载的国家消防救援局全国年度新闻发布会实录。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
SOURCES = {2024: 'https://js.119.gov.cn/202501/jsxfww-menu-zxft-zxftlb_c_a9f51911e874498586b7.html', 2025: 'https://js.119.gov.cn/202603/jsxfww-menu-zxft-zxftlb_c_4093535d4c52493d9e46ec54cc9cbbec.html'}

def catalog():
    return {'source': '国家消防救援局年度火灾形势发布会，江苏省消防救援总队官网转载', 'items': [{'year': y, 'url': url, 'type': '新闻发布会实录'} for y, url in sorted(SOURCES.items(), reverse=True)], 'note': '固定已验证两次发布会实录，不是全国火灾数据库或逐起事故清单。'}

def search(year, keyword='', limit=30):
    if isinstance(year, bool) or not isinstance(year, int) or year not in SOURCES:
        raise ValueError('year 须为 2024 或 2025')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词最多 100 字')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 200):
        raise ValueError('limit 须为 1–200')
    with requests.get(SOURCES[year], timeout=(10, 25), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('上游重定向')
        raw = bytearray()
        for part in r.iter_content(65536):
            raw.extend(part)
            if len(raw) > 4000000:
                raise ValueError('正文过大')
    s = BeautifulSoup(bytes(raw), 'html.parser')
    body = s.select_one('.newtalk-right-content')
    if not body:
        raise ValueError('未识别实录正文')
    paras = [re.sub('\\s+', ' ', p.get_text('', strip=True)).strip() for p in body.select('p')]
    paras = [p for p in paras if p]
    if len(paras) < 10:
        raise ValueError('实录正文不足')
    matches = [{'paragraph': i + 1, 'text': p} for i, p in enumerate(paras) if keyword in p]
    return {'source': '国家消防救援局年度火灾形势发布会，江苏省消防救援总队官网转载', 'year': year, 'url': SOURCES[year], 'keyword': keyword, 'matched_paragraphs': len(matches), 'hits': matches[:limit], 'note': '原文为新闻发布会实录，含不同时间范围、提问和案例，不能视为可直接汇总的逐笔记录；接报火灾、扑救警情和自然灾害数据口径不同。2024实录的火灾直接财产损失77.4亿元，与2025实录85.3亿元及同比上升1.8%存在计算不一致，未核实原因，比较前应核官方修订。'}
