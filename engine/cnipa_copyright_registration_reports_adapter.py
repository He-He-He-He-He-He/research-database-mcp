"""国家知识产权局网站公开的全国著作权登记情况摘报。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
SOURCES = {2019: ('https://www.cnipa.gov.cn/art/2020/3/25/art_1413_151085.html', '国家版权局通报的转述'), 2022: ('https://www.cnipa.gov.cn/art/2023/3/28/art_1413_187015.html', '国家版权局通报的转述'), 2023: ('https://www.cnipa.gov.cn/art/2024/2/26/art_1413_206497.html', '国家版权局通报全文转载'), 2024: ('https://www.cnipa.gov.cn/art/2025/4/26/art_53_199324.html', '中国知识产权保护状况白皮书发布摘要，数值有四舍五入'), 2025: ('https://www.cnipa.gov.cn/art/2026/5/7/art_53_206320.html', '中国知识产权保护状况白皮书发布摘要，数值有四舍五入')}

def catalog():
    return {'source': '国家知识产权局公开的全国著作权登记信息', 'items': [{'year': y, 'url': v[0], 'source_type': v[1]} for y, v in sorted(SOURCES.items(), reverse=True)], 'note': '固定样本，部分是白皮书或新闻摘要，只有 2023 标为通报全文，不是完整年度目录。'}

def search(year, keyword='著作权', limit=20):
    if isinstance(year, bool) or not isinstance(year, int) or year not in SOURCES:
        raise ValueError('支持 2019、2022–2025')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词最多 100 字')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('limit 须为 1–100')
    u, kind = SOURCES[year]
    with requests.get(u, timeout=(10, 25), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('官方来源发生重定向')
        raw = bytearray()
        for chunk in r.iter_content(65536):
            raw.extend(chunk)
            if len(raw) > 2000000:
                raise ValueError('来源超出大小上限')
    soup = BeautifulSoup(bytes(raw), 'html.parser')
    body = soup.select_one('.article-content')
    if not body:
        raise ValueError('未识别正文')
    paras = [re.sub('\\s+', ' ', p.get_text('', strip=True)).strip() for p in body.select('p')]
    paras = [p for p in paras if p]
    if not paras:
        raise ValueError('正文为空')
    hits = [{'paragraph': i + 1, 'text': p} for i, p in enumerate(paras) if keyword in p]
    return {'source': '国家知识产权局公开的全国著作权登记信息', 'year': year, 'url': u, 'source_type': kind, 'keyword': keyword, 'matched_paragraphs': len(hits), 'hits': hits[:limit], 'note': '原文摘段，按原单位和精度保留；新闻摘要与完整登记通报范围不同。作品、计算机软件及质权登记为不同概念，登记量不等于全部创作数量或版权产业增加值。'}
