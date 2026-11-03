"""中国视听大数据国产电视剧收视报告公开网页正文查询。"""
import release_runtime
from pathlib import Path
from nrta_broadcast_statistics_adapters import _Paragraphs
ROOT = Path(__file__).parent
REPORTS = {'2025': ('CVB2025国产电视剧收视报告.html', 'https://www.nrta.gov.cn/art/2025/12/26/art_114_72192.html'), '2026h1': ('CVB2026上半年国产电视剧收视报告.html', 'https://www.nrta.gov.cn/art/2026/7/11/art_114_73688.html')}

def search_cvb_drama_reports(period, keyword=''):
    """按原文段落查询 2025 年或 2026 上半年国产电视剧收视报告。"""
    if period not in REPORTS:
        raise ValueError('period 应为 2025 或 2026h1')
    filename, source_url = REPORTS[period]
    parser = _Paragraphs()
    parser.feed((ROOT / filename).read_text(encoding='utf-8'))
    if not parser.paragraphs:
        raise ValueError('报告正文未识别')
    keyword = keyword.strip()
    return [{'period': period, 'paragraph': i, 'text': t, 'source_url': source_url} for i, t in enumerate(parser.paragraphs, 1) if not keyword or keyword in t]
