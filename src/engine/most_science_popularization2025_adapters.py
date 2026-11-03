"""科技部 2025 年度全国科普统计数据原文查询。"""
import release_runtime
from pathlib import Path
from china_reading_survey_adapters import _Paragraphs
HTML_PATH = Path(__file__).with_name('科技部2025年度全国科普统计数据.html')
SOURCE_URL = 'https://www.most.gov.cn/kjbgz/202609/t20260920_197370.html'

def search_science_popularization2025(keyword=''):
    """返回包含关键词的原文段落，空词返回全部。"""
    parser = _Paragraphs()
    parser.feed(HTML_PATH.read_text(encoding='utf-8'))
    if len(parser.paragraphs) != 7:
        raise ValueError('科技部科普统计正文段落数量异常')
    keyword = keyword.strip()
    return [{'paragraph': i, 'text': t, 'reference_year': 2025, 'publication_year': 2026, 'source_url': SOURCE_URL} for i, t in enumerate(parser.paragraphs, 1) if not keyword or keyword in t]
