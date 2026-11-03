"""科技部 2025 年科普统计调查方案及表格文本检索。"""
import release_runtime
from pathlib import Path
import re
ROOT = Path(__file__).parent
SOURCES = {'plan': ('2025年度全国科普统计调查方案_提取文本.txt', 'https://www.most.gov.cn/xxgk/xinxifenlei/fdzdgknr/qtwj/qtwj2026/202602/P020260204354861770617.doc'), 'form': ('2025年度科普统计调查表_提取文本.txt', 'https://www.most.gov.cn/xxgk/xinxifenlei/fdzdgknr/qtwj/qtwj2026/202602/P020260204354861803084.doc')}
NOTICE = 'https://www.most.gov.cn/xxgk/xinxifenlei/fdzdgknr/qtwj/qtwj2026/202602/t20260204_195856.html'

def search_science_survey_schema2025(keyword, document='form', limit=20):
    """检索 DOC 转换文本并返回每处附近文字；不重建表格。"""
    if document not in SOURCES:
        raise ValueError('document 应为 plan 或 form')
    if not keyword.strip():
        raise ValueError('请输入关键词')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 100):
        raise ValueError('limit 应为 1 至 100 的整数')
    path, url = SOURCES[document]
    source = (ROOT / path).read_text(encoding='utf-8')
    matches = list(re.finditer(re.escape(keyword.strip()), source, re.IGNORECASE))
    return {'document': document, 'matched_occurrences': len(matches), 'limit': limit, 'source_url': url, 'notice_url': NOTICE, 'results': [{'character_offset': m.start(), 'context': source[max(0, m.start() - 180):min(len(source), m.end() + 180)]} for m in matches[:limit]], 'scope': 'DOC 转纯文本会丢失表格布局及部分格式，请对照原 DOC'}
