"""2021 年新闻出版产业分析报告 PDF 页级全文检索。"""
import release_runtime
from functools import lru_cache
from pathlib import Path
import re
PDF_PATH = Path(__file__).with_name('2021年新闻出版产业分析报告.pdf')
SOURCE_URL = 'https://www.nppa.gov.cn/xxgk/fdzdgknr/tjxx/202305/P020230530667517704140.pdf'
INDEX_URL = 'https://www.nppa.gov.cn/xxgk/fdzdgknr/tjxx/'

@lru_cache(maxsize=1)
def _pages():
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError('需要安装可选依赖 pypdf') from e
    reader = PdfReader(str(PDF_PATH))
    if len(reader.pages) != 48:
        raise ValueError('PDF 页数异常')
    return tuple((page.extract_text() or '' for page in reader.pages))

def search_publishing_analysis2021(keyword, limit=20):
    """返回匹配关键词的 PDF 页码及原页文字。"""
    needle = re.sub('\\s+', '', keyword)
    if not needle:
        raise ValueError('请输入关键词')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 48):
        raise ValueError('limit 应为 1 至 48 的整数')
    rows = [{'pdf_page': i, 'text': t, 'reference_year': 2021, 'source_url': SOURCE_URL} for i, t in enumerate(_pages(), 1) if needle in re.sub('\\s+', '', t)]
    return {'results': rows[:limit], 'matched_pages': len(rows), 'limit': limit, 'scope': '仅 PDF 文本层；图表文字顺序及指标口径须参照原页'}
