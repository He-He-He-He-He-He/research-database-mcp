"""国家电影局网站发布的年度电影票房与城市院线观影人次。"""
import release_runtime
from pathlib import Path
import re
from china_reading_survey_adapters import _Paragraphs
ROOT = Path(__file__).parent
SOURCES = {2024: 'https://www.chinafilm.gov.cn/xwzx/gzdt/202501/t20250102_879736.html', 2025: 'https://www.chinafilm.gov.cn/xwzx/gzdt/202601/t20260105_944809.html'}

def annual_film_boxoffice(year):
    """提取年度票房、国产片票房份额及城市院线观影人次。"""
    if year not in SOURCES:
        raise ValueError('year 应为 2024 或 2025')
    p = _Paragraphs()
    p.feed((ROOT / f'国家电影局{year}年电影票房发布.html').read_text(encoding='utf-8'))
    candidates = [t for t in p.paragraphs if '城市院线观影人次' in t and '国产影片票房' in t]
    if len(candidates) != 1:
        raise ValueError('官方报道数据段落无法唯一定位')
    t = candidates[0]
    patterns = {'boxoffice_yi_yuan': '电影票房为([\\d.]+)亿元', 'domestic_boxoffice_yi_yuan': '国产影片票房为([\\d.]+)亿元', 'domestic_share_percent': '(?:国产影片票房为[\\d.]+亿元[^。；]*?占比为)([\\d.]+)%', 'urban_admissions_yi': '城市院线观影人次为([\\d.]+)亿'}
    result = {}
    for name, pattern in patterns.items():
        m = re.search(pattern, t)
        if not m:
            raise ValueError(f'无法解析字段: {name}')
        result[name] = m.group(1)
    return {'year': year, **result, 'source_url': SOURCES[year], 'source_paragraph': t, 'note': '票房单位亿元；观影为城市院线亿人次，非去重人数；份额为百分比。'}
