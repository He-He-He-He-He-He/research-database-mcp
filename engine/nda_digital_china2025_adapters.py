"""国家数据局《数字中国发展报告（2025年）》原 PDF 检索。"""
import release_runtime
from functools import lru_cache
from pathlib import Path
import re
PDF_PATH = Path(__file__).with_name('国家数据局数字中国发展报告2025.pdf')
SOURCE_URL = 'https://www.nda.gov.cn/sjj/swdt/xwfb/0608/ff808081-9e81e648-019e-a78ceae4-00c3.pdf'

@lru_cache(maxsize=1)
def _pages():
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError('需要安装可选依赖 pypdf') from e
    reader = PdfReader(str(PDF_PATH))
    if len(reader.pages) != 52:
        raise ValueError('PDF 页数异常')
    return tuple((p.extract_text() or '' for p in reader.pages))

def search_digital_china2025(keyword, limit=20):
    """按 PDF 文本层搜索，保留原页及 PDF 页码。"""
    needle = re.sub('\\s+', '', keyword)
    if not needle:
        raise ValueError('请输入关键词')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 52):
        raise ValueError('limit 应为 1 至 52 的整数')
    rows = [{'pdf_page': n, 'text': t, 'report_year': 2025, 'publication_year': 2026, 'source_url': SOURCE_URL} for n, t in enumerate(_pages(), 1) if needle in re.sub('\\s+', '', t)]
    return {'results': rows[:limit], 'matched_pages': len(rows), 'limit': limit, 'scope': '只检索 PDF 文本层；数据来源及时点各异，应核对原报告和引文'}
