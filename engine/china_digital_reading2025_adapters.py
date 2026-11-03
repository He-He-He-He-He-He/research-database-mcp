"""中国音数协 2025 数字阅读报告发布材料的原文段落查询。"""
import release_runtime
from pathlib import Path
from china_reading_survey_adapters import _Paragraphs
HTML_PATH = Path(__file__).with_name('2025年度中国数字阅读报告发布.html')
SOURCE_URL = 'https://www.nationalreading.gov.cn/ydzg/dfdt/202604/t20260420_985574.html'

def search_digital_reading2025(keyword=''):
    """查询协会发布材料的文本；图片和完整底层数据不在检索范围。"""
    parser = _Paragraphs()
    parser.feed(HTML_PATH.read_text(encoding='utf-8'))
    if len(parser.paragraphs) < 40:
        raise ValueError('报告发布材料正文解析异常')
    keyword = keyword.strip()
    return [{'paragraph': i, 'text': t, 'reference_year': 2025, 'publication_year': 2026, 'source_url': SOURCE_URL, 'source_type': '协会报告发布材料'} for i, t in enumerate(parser.paragraphs, 1) if not keyword or keyword in t]
