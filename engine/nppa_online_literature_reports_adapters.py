"""国家新闻出版署网站关于网络文学年度报告的报道正文索引。"""
import release_runtime
from pathlib import Path
from china_reading_survey_adapters import _Paragraphs
ROOT = Path(__file__).parent
SOURCES = {2024: 'https://www.nppa.gov.cn/xxfb/ywdt/202507/t20250718_922584.html', 2025: 'https://www.nppa.gov.cn/xxfb/ywdt/202610/t20261016_1012682.html'}

def search_online_literature_reports(year, keyword=''):
    """搜索 2024 或 2025 年报告相关报道的原文段落。"""
    if year not in SOURCES:
        raise ValueError('year 应为 2024 或 2025')
    parser = _Paragraphs()
    parser.feed((ROOT / f'{year}网络文学发展报告报道.html').read_text(encoding='utf-8'))
    if not parser.paragraphs:
        raise ValueError('报道正文未识别到段落')
    keyword = keyword.strip()
    return [{'report_year': year, 'paragraph': i, 'text': t, 'source_url': SOURCES[year], 'source_type': '报告成果的新闻报道'} for i, t in enumerate(parser.paragraphs, 1) if not keyword or keyword in t]
