"""2025 年度国家老龄事业发展公报原 PDF 查询。"""
import release_runtime
from functools import lru_cache
from pathlib import Path
import re
PDF_PATH = Path(__file__).with_name('2025年度国家老龄事业发展公报.pdf')
SOURCE_URL = 'https://www.hunan.gov.cn/zqt/zcsd/202608/34038369/files/6d6b022f114749ca82aacaaf28fb0cc0.pdf'
CATALOG_URL = 'https://www.hunan.gov.cn/zqt/zcsd/202608/t20260803_34038369.html'

@lru_cache(maxsize=1)
def _pages():
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError('需要安装可选依赖 pypdf') from e
    reader = PdfReader(str(PDF_PATH))
    if len(reader.pages) != 16:
        raise ValueError('PDF 页数异常')
    return tuple((p.extract_text() or '' for p in reader.pages))

def search_aging_bulletin2025(keyword, limit=16):
    """按文字搜索原公报 PDF，返回完整命中页。"""
    needle = re.sub('\\s+', '', keyword)
    if not needle:
        raise ValueError('请输入关键词')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 16):
        raise ValueError('limit 应为 1 至 16 的整数')
    rows = [{'pdf_page': n, 'text': t, 'reference_year': 2025, 'source_url': SOURCE_URL, 'catalog_url': CATALOG_URL} for n, t in enumerate(_pages(), 1) if needle in re.sub('\\s+', '', t)]
    return {'results': rows[:limit], 'matched_pages': len(rows), 'limit': limit, 'scope': '只检索 PDF 可提取文本；图像、图表未做 OCR，按原文核对指标口径'}
