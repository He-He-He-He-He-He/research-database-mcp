"""国家药品不良反应监测中心年度报告正文检索。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
SOURCES = {2022: 'https://www.cdr-adr.org.cn/drug_1/aqjs_1/drug_aqjs_sjbg/202303/t20230324_50019.html', 2023: 'https://www.cdr-adr.org.cn/drug_1/aqjs_1/drug_aqjs_sjbg/202403/t20240326_50614.html', 2024: 'https://www.cdr-adr.org.cn/center_news/202504/t20250407_51076.html', 2025: 'https://www.cdr-adr.org.cn/center_news/202604/t20260427_51496.html'}

def catalog():
    return {'source': '国家药品不良反应监测中心年度报告', 'items': [{'year': y, 'title': f'国家药品不良反应监测年度报告（{y}年）', 'url': u} for y, u in sorted(SOURCES.items(), reverse=True)], 'note': '固定已核验的四个官方报告，非完整历史目录。'}

def search(year, keyword='', limit=30):
    if isinstance(year, bool) or not isinstance(year, int) or year not in SOURCES:
        raise ValueError('year 须为 2022–2025')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词最多 100 字')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 200):
        raise ValueError('limit 须为 1–200')
    url = SOURCES[year]
    with requests.get(url, timeout=(10, 25), allow_redirects=False, stream=True) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('来源重定向')
        raw = bytearray()
        for chunk in r.iter_content(65536):
            raw.extend(chunk)
            if len(raw) > 3000000:
                raise ValueError('正文超过大小上限')
    s = BeautifulSoup(bytes(raw), 'html.parser')
    body = s.select_one('.TRS_Editor')
    if not body:
        raise ValueError('未识别正文')
    for e in body.select('style,script'):
        e.decompose()
    segments = [re.sub('\\s+', ' ', p.get_text('', strip=True)).strip() for p in body.select('p,div') if p.name == 'p' or (not p.select('p,div') and p.find_parent('p') is None)]
    segments = [x for x in segments if x]
    if len(segments) < 10:
        raise ValueError('正文结构无效')
    hits = [{'segment': i + 1, 'text': p} for i, p in enumerate(segments) if keyword in p]
    return {'source': '国家药品不良反应监测中心年度报告', 'year': year, 'url': url, 'keyword': keyword, 'matched_segments': len(hits), 'hits': hits[:limit], 'note': '保留原文段落；图片图表未识别，表格可能拆为单元格。报告数为监测网络收到的不良反应/事件报告，不等于发生人数、真实发生率或已证实因果关系，也不能凭报告数判断药品风险高低；需结合使用量、报告机制及专业评价。'}
