"""国家医保局 2023/2024 年全国医疗保障事业发展统计公报。"""
import release_runtime
from pathlib import Path
import re
from nrta_broadcast_statistics_adapters import _Paragraphs
ROOT = Path(__file__).parent
SOURCES = {2023: 'https://www.nhsa.gov.cn/art/2024/7/25/art_7_13340.html', 2024: 'https://www.nhsa.gov.cn/art/2025/7/14/art_7_17248.html'}

def search_health_insurance_history(year, keyword=''):
    """按原文段落检索年报并返回可提取的编号注释。"""
    if year not in SOURCES:
        raise ValueError('year 应为 2023 或 2024')
    p = _Paragraphs()
    p.feed((ROOT / f'{year}年全国医疗保障事业发展统计公报.html').read_text(encoding='utf-8'))
    if len(p.paragraphs) < 50:
        raise ValueError('公报正文解析异常')
    keyword = keyword.strip()
    rows = [{'reference_year': year, 'paragraph': i, 'text': t, 'source_url': SOURCES[year]} for i, t in enumerate(p.paragraphs, 1) if not keyword or keyword in t]
    return {'reference_year': year, 'publication_year': year + 1, 'source_url': SOURCES[year], 'results': rows, 'footnotes': [t for t in p.paragraphs if re.match('^\\[\\d+\\]', t)]}
