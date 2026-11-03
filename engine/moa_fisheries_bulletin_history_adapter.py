"""农业农村部全国渔业经济统计公报 2020–2025 正文检索。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
SOURCES = {2020: 'https://yyj.moa.gov.cn/gzdt/202107/t20210728_6372958.htm', 2021: 'https://yyj.moa.gov.cn/gzdt/202207/t20220721_6405222.htm', 2022: 'https://yyj.moa.gov.cn/kjzl/202306/t20230628_6431131.htm', 2023: 'https://yyj.moa.gov.cn/gzdt/202407/t20240705_6458486.htm', 2024: 'https://yyj.moa.gov.cn/gzdt/202507/t20250707_6475475.htm', 2025: 'https://yyj.moa.gov.cn/gzdt/202607/t20260727_6486230.htm'}

def catalog():
    return {'source': '农业农村部全国渔业经济统计公报', 'items': [{'year': y, 'url': url, 'title': f'{y}年全国渔业经济统计公报'} for y, url in sorted(SOURCES.items(), reverse=True)], 'note': '固定六年已核验官方文件，非全部历史目录。'}

def search(year, keyword='', limit=30):
    if isinstance(year, bool) or not isinstance(year, int) or year not in SOURCES:
        raise ValueError('年份须为 2020–2025')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词最多 100 字')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('limit 须为 1–100')
    url = SOURCES[year]
    with requests.get(url, timeout=(10, 25), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('官方来源重定向')
        raw = bytearray()
        for chunk in r.iter_content(65536):
            raw.extend(chunk)
            if len(raw) > 3000000:
                raise ValueError('正文过大')
    s = BeautifulSoup(bytes(raw), 'html.parser')
    body = s.select_one('.TRS_Editor')
    if not body:
        raise ValueError('未识别正文')
    for e in body.select('script,style'):
        e.decompose()
    paragraphs = [re.sub('\\s+', ' ', p.get_text('', strip=True)).strip() for p in body.select('p,div') if p.name == 'p' or (not p.select('p,div') and p.find_parent('p') is None)]
    paragraphs = [p for p in paragraphs if p]
    if len(paragraphs) < 5:
        raise ValueError('正文结构无效')
    found = [{'paragraph': i + 1, 'text': p} for i, p in enumerate(paragraphs) if keyword in p]
    return {'source': '农业农村部全国渔业经济统计公报', 'year': year, 'url': url, 'keyword': keyword, 'matched_paragraphs': len(found), 'hits': found[:limit], 'note': '返回原文段落，不自动推算；图表和图片未识别。渔业经济总产值、渔业产值、水产品产量及从业人口均为不同指标，跨年统计口径需核原文。'}
