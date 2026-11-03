"""CNNIC《生成式人工智能应用发展报告（2025）》PDF 页级查询。"""
import release_runtime
from functools import lru_cache
from pathlib import Path
import re
PDF_PATH = Path(__file__).with_name('CNNIC生成式人工智能应用发展报告2025.pdf')
SOURCE_URL = 'https://www.cnnic.cn/NMediaFile/2025/1021/MAIN1761038973801E6DI0GFPDE.pdf'
DETAIL_URL = 'https://www.cnnic.cn/n4/2025/1021/c88-11391.html'

@lru_cache(maxsize=1)
def _pages():
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError('需要安装可选依赖 pypdf') from e
    reader = PdfReader(str(PDF_PATH))
    if len(reader.pages) != 63:
        raise ValueError('PDF 页数异常')
    return tuple((page.extract_text() or '' for page in reader.pages))

def search_cnnic_ai_report2025(keyword, limit=20):
    """返回匹配 PDF 文本的页码和完整页文字。"""
    needle = re.sub('\\s+', '', keyword)
    if not needle:
        raise ValueError('请输入关键词')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 63):
        raise ValueError('limit 应为 1 至 63 的整数')
    rows = [{'pdf_page': i, 'text': text, 'source_url': SOURCE_URL, 'detail_url': DETAIL_URL, 'publication_year': 2025} for i, text in enumerate(_pages(), 1) if needle in re.sub('\\s+', '', text)]
    return {'results': rows[:limit], 'matched_pages': len(rows), 'limit': limit, 'scope': '仅 PDF 文本层；各数据时点、分母及来源不同，参照原文及注释'}
