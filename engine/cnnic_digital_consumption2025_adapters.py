"""CNNIC 数字消费发展报告（2025）原始 PDF 页级检索。"""
import release_runtime
from functools import lru_cache
from pathlib import Path
import re
PDF_PATH = Path(__file__).with_name('CNNIC数字消费发展报告2025.pdf')
SOURCE_URL = 'https://www.cnnic.cn/NMediaFile/2026/0107/MAIN1767768003377ZLVKROPRZX.pdf'
DETAIL_URL = 'https://www.cnnic.cn/n4/2025/1226/c88-11445.html'

@lru_cache(maxsize=1)
def _pages():
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError('需要安装可选依赖 pypdf') from e
    reader = PdfReader(str(PDF_PATH))
    if len(reader.pages) != 58:
        raise ValueError('PDF 页数异常')
    return tuple((page.extract_text() or '' for page in reader.pages))

def search_cnnic_digital_consumption2025(keyword, limit=20):
    """按 PDF 可提取文本定位页码，返回整页内容及来源。"""
    needle = re.sub('\\s+', '', keyword)
    if not needle:
        raise ValueError('请输入关键词')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 58):
        raise ValueError('limit 应为 1 至 58 的整数')
    rows = [{'pdf_page': i, 'text': text, 'source_url': SOURCE_URL, 'detail_url': DETAIL_URL, 'report_year': 2025} for i, text in enumerate(_pages(), 1) if needle in re.sub('\\s+', '', text)]
    return {'results': rows[:limit], 'matched_pages': len(rows), 'limit': limit, 'scope': '仅 PDF 文本层，图片未做 OCR；各指标口径及时点以原文为准'}
