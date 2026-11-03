"""第 57 次中国互联网络发展状况统计报告官方 PDF 页级全文查询。"""
import release_runtime
from functools import lru_cache
from pathlib import Path
import re
PDF_PATH = Path(__file__).with_name('第57次中国互联网络发展状况统计报告.pdf')
SOURCE_URL = 'https://www.cnnic.cn/NMediaFile/2026/0304/MAIN1772588317069TUXN3827X8.pdf'
DETAIL_URL = 'https://www.cnnic.cn/n4/2026/0304/c88-11549.html'

@lru_cache(maxsize=1)
def _pages():
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError('需要安装可选依赖 pypdf') from e
    reader = PdfReader(str(PDF_PATH))
    if len(reader.pages) != 83:
        raise ValueError('PDF 页数异常')
    return tuple((page.extract_text() or '' for page in reader.pages))

def search_cnnic_report57(keyword, limit=20):
    """搜索 PDF 可提取文本；结果包含一基页码和该页完整提取文本。"""
    needle = re.sub('\\s+', '', keyword)
    if not needle:
        raise ValueError('请输入关键词')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 83):
        raise ValueError('limit 应为 1 至 83 的整数')
    results = []
    for number, page in enumerate(_pages(), 1):
        if needle in re.sub('\\s+', '', page):
            results.append({'pdf_page': number, 'text': page, 'source_url': SOURCE_URL, 'detail_url': DETAIL_URL, 'round': 57, 'reference_time': '2025-12', 'publication_year': 2026})
    return {'results': results[:limit], 'matched_pages': len(results), 'limit': limit, 'scope': '仅 PDF 文本层，图表图片未做 OCR；结果以原页为准'}
