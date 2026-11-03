"""全国国民阅读调查 2023、2024 指标报告正文检索。"""
import release_runtime
from pathlib import Path
from china_reading_survey_adapters import _Paragraphs
ROOT = Path(__file__).parent
REPORTS = {2023: ('第二十一次全国国民阅读调查成果.html', 'https://www.nationalreading.gov.cn/wzzt/2024qmyddh/cgfb/202404/t20240424_844854.html'), 2024: ('第二十二次全国国民阅读调查成果.html', 'https://www.nationalreading.gov.cn/wzzt/2025qmyddh/cgfb/202504/t20250424_892768.html')}

def search_reading_survey_history(year, keyword=''):
    """搜索对应阅读状况年度的发布文本。"""
    if year not in REPORTS:
        raise ValueError('year 应为 2023 或 2024')
    filename, url = REPORTS[year]
    parser = _Paragraphs()
    parser.feed((ROOT / filename).read_text(encoding='utf-8'))
    if len(parser.paragraphs) < 30:
        raise ValueError('调查正文未完整识别')
    keyword = keyword.strip()
    return [{'reference_year': year, 'publication_year': year + 1, 'paragraph': i, 'text': t, 'source_url': url} for i, t in enumerate(parser.paragraphs, 1) if not keyword or keyword in t]
