"""教育部 2023、2024 年全国教育事业发展统计公报原文。"""
import release_runtime
from pathlib import Path
import re
from most_science_popularization_history_adapters import _Content
ROOT = Path(__file__).parent
SOURCES = {2023: 'https://www.moe.gov.cn/jyb_sjzl/sjzl_fztjgb/202410/t20241024_1159002.html', 2024: 'https://www.moe.gov.cn/jyb_sjzl/sjzl_fztjgb/202506/t20250611_1193760.html'}

def search_education_bulletin_history(year, keyword=''):
    """搜索教育年度公报原段，并返回全部编号注释。"""
    if year not in SOURCES:
        raise ValueError('year 应为 2023 或 2024')
    p = _Content()
    p.feed((ROOT / f'{year}年全国教育事业发展统计公报.html').read_text(encoding='utf-8'))
    if len(p.paragraphs) < 50:
        raise ValueError('公报正文解析异常')
    keyword = keyword.strip()
    rows = [{'reference_year': year, 'paragraph': i, 'text': t, 'source_url': SOURCES[year]} for i, t in enumerate(p.paragraphs, 1) if not keyword or keyword in t]
    return {'reference_year': year, 'publication_year': year + 1, 'source_url': SOURCES[year], 'results': rows, 'footnotes': [t for t in p.paragraphs if re.match('^\\[\\d+\\]', t)]}
