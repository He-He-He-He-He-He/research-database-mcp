"""教育部 2025 年全国教育事业发展统计公报原文索引。"""
import release_runtime
from pathlib import Path
import re
from most_science_popularization_history_adapters import _Content
HTML_PATH = Path(__file__).with_name('2025年全国教育事业发展统计公报.html')
SOURCE_URL = 'https://www.moe.gov.cn/jyb_sjzl/sjzl_fztjgb/202607/t20260706_1442870.html'

def search_education_bulletin2025(keyword=''):
    """查询原文段落并返回全部编号统计注释。"""
    p = _Content()
    p.feed(HTML_PATH.read_text(encoding='utf-8'))
    if len(p.paragraphs) < 50:
        raise ValueError('公报正文未能完整识别')
    keyword = keyword.strip()
    rows = [{'paragraph': i, 'text': t, 'source_url': SOURCE_URL, 'reference_year': 2025} for i, t in enumerate(p.paragraphs, 1) if not keyword or keyword in t]
    notes = [t for t in p.paragraphs if re.match('^\\[\\d+\\]', t)]
    return {'reference_year': 2025, 'publication_year': 2026, 'source_url': SOURCE_URL, 'results': rows, 'footnotes': notes}
