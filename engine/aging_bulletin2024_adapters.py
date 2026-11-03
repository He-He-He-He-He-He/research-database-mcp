"""2024 年度国家老龄事业发展公报原 PDF 查询。"""
import release_runtime
from functools import lru_cache
from pathlib import Path
import re
PDF_PATH = Path(__file__).with_name('2024年度国家老龄事业发展公报.pdf')
SOURCE_URL = 'https://www.gov.cn/lianbo/bumen/202507/P020250725463987010460.pdf'
CATALOG_URL = 'https://www.gov.cn/lianbo/bumen/202507/content_7033724.htm'

@lru_cache(maxsize=1)
def _pages():
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError('需要安装可选依赖 pypdf') from e
    reader = PdfReader(str(PDF_PATH))
    if len(reader.pages) != 22:
        raise ValueError('PDF 页数异常')
    return tuple((p.extract_text() or '' for p in reader.pages))

def search_aging_bulletin2024(keyword, limit=22):
    """按文字搜索原公报 PDF，返回完整命中页。"""
    needle = re.sub('\\s+', '', keyword)
    if not needle:
        raise ValueError('请输入关键词')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 22):
        raise ValueError('limit 应为 1 至 22 的整数')
    rows = [{'pdf_page': n, 'text': t, 'reference_year': 2024, 'source_url': SOURCE_URL, 'catalog_url': CATALOG_URL} for n, t in enumerate(_pages(), 1) if needle in re.sub('\\s+', '', t)]
    return {'results': rows[:limit], 'matched_pages': len(rows), 'limit': limit, 'scope': '只检索 PDF 可提取文本；图像、图表未做 OCR，按原文核对指标口径'}
