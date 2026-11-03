"""Selected national criminal prosecution statistics from SPP white papers."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
SOURCES = {2024: 'https://www.spp.gov.cn/xwfbh/wsfbh/202503/t20250309_688590.shtml', 2025: 'https://www.spp.gov.cn/xwfbh/wsfbh/202603/t20260310_722849.shtml'}

def catalog():
    return [{'year': y, 'url': u} for y, u in sorted(SOURCES.items(), reverse=True)]

def report(year):
    if type(year) is not int or year not in SOURCES:
        raise ValueError('supported years: 2024 or 2025')
    with requests.get(SOURCES[year], timeout=(10, 35), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        raw = bytearray()
        for c in r.iter_content(65536):
            raw.extend(c)
            if len(raw) > 3000000:
                raise ValueError('source too large')
    soup = BeautifulSoup(bytes(raw), 'html.parser')
    body = soup.select_one('.Custom_UnionStyle')
    if not body:
        raise ValueError('source body missing')
    text = body.get_text('', strip=True)
    text = re.sub('\\s+', '', text)
    results = {}
    pairs = {'review_arrest': '受理审查逮捕各类犯罪(\\d+)件(\\d+)人', 'review_prosecution': '受理审查起诉各类犯罪(\\d+)件(\\d+)人'}
    for name, pat in pairs.items():
        hits = list(re.finditer(pat, text))
        if len(hits) == 1:
            m = hits[0]
            results[name] = {'cases': int(m[1]), 'persons': int(m[2]), 'source_excerpt': m[0]}
    singles = {'approved_arrests': '批准和决定逮捕(\\d+)人', 'decided_prosecution': '审查后决定起诉(\\d+)人'}
    for name, pat in singles.items():
        hits = list(re.finditer(pat, text))
        if len(hits) == 1:
            m = hits[0]
            results[name] = {'persons': int(m[1]), 'source_excerpt': m[0]}
    if not results:
        raise ValueError('no unambiguous selected figures')
    return {'source': '最高人民检察院刑事检察工作白皮书', 'year': year, 'url': SOURCES[year], 'metrics': results, 'note': '各项统计对象和办案环节不同；受理、决定人数不能简单直接相减或理解为审判结果。'}
