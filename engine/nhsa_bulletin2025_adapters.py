"""国家医保局 2025 年全国医疗保障事业发展统计公报。"""
import release_runtime
from pathlib import Path
import re
from nrta_broadcast_statistics_adapters import _Paragraphs
HTML_PATH = Path(__file__).with_name('2025年全国医疗保障事业发展统计公报.html')
SOURCE_URL = 'https://www.nhsa.gov.cn/art/2026/7/16/art_7_21451.html'

def search_health_insurance_bulletin2025(keyword=''):
    """按子串搜索公报正文；同时返回可提取的原文注释。"""
    p = _Paragraphs()
    p.feed(HTML_PATH.read_text(encoding='utf-8'))
    if len(p.paragraphs) < 50:
        raise ValueError('公报正文解析异常')
    keyword = keyword.strip()
    rows = [{'paragraph': i, 'text': t, 'source_url': SOURCE_URL, 'reference_year': 2025} for i, t in enumerate(p.paragraphs, 1) if not keyword or keyword in t]
    notes = [t for t in p.paragraphs if re.match('^\\[\\d+\\]', t)]
    return {'reference_year': 2025, 'publication_year': 2026, 'source_url': SOURCE_URL, 'results': rows, 'footnotes': notes}
