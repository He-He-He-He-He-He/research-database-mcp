"""国家电影局网站暑期档电影票房公开数据。"""
import release_runtime
from pathlib import Path
import re
from china_reading_survey_adapters import _Paragraphs
ROOT = Path(__file__).parent
SOURCES = {2025: 'https://www.chinafilm.gov.cn/xwzx/gzdt/202509/t20250904_928990.html', 2026: 'https://www.chinafilm.gov.cn/xwzx/hyzx/202609/t20260902_1006502.html'}

def summer_film_boxoffice(year):
    """读取年度暑期档票房、观影人次和国产片份额。"""
    if year not in SOURCES:
        raise ValueError('year 应为 2025 或 2026')
    parser = _Paragraphs()
    parser.feed((ROOT / f'国家电影局{year}暑期档票房.html').read_text(encoding='utf-8'))
    rows = [t for t in parser.paragraphs if f'{year}年暑期档电影票房为' in t]
    if len(rows) != 1:
        raise ValueError('无法唯一定位官方报道数据段')
    text = rows[0]
    fields = {}
    for name, pattern in {'boxoffice_yi_yuan': '暑期档电影票房为([\\d.]+)亿元', 'admissions_yi': '观影人次为([\\d.]+)亿', 'domestic_share_percent': '国产影片票房占比为([\\d.]+)%'}.items():
        match = re.search(pattern, text)
        if not match:
            raise ValueError(f'无法解析字段: {name}')
        fields[name] = match.group(1)
    return {'year': year, 'period': '暑期档', **fields, 'source_url': SOURCES[year], 'source_paragraph': text, 'note': '暑期档并非全年；观影人次非去重人数。'}
