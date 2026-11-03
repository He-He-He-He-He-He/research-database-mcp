"""CNNIC 2016年中国社交应用用户行为研究报告PDF 页级查询。"""
import release_runtime
from functools import lru_cache
from pathlib import Path
import re
PDF_PATH = Path(__file__).with_name('CNNIC2016年中国社交应用用户行为研究报告.pdf')
SOURCE_URL = 'https://www.cnnic.cn/NMediaFile/old_attach/P020180103485975797840.pdf'
DETAIL_URL = 'https://www.cnnic.cn/n4/2022/0401/c123-1119.html'

@lru_cache(maxsize=1)
def _pages():
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError('需要安装可选依赖 pypdf') from e
    reader = PdfReader(str(PDF_PATH))
    if len(reader.pages) != 42:
        raise ValueError('PDF 页数异常')
    return tuple((page.extract_text() or '' for page in reader.pages))

def search_cnnic_social2016(keyword, limit=20):
    """返回匹配 PDF 文本的页码和完整页文字。"""
    needle = re.sub('\\s+', '', keyword)
    if not needle:
        raise ValueError('请输入关键词')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 42):
        raise ValueError('limit 应为 1 至 42 的整数')
    rows = [{'pdf_page': i, 'text': text, 'source_url': SOURCE_URL, 'detail_url': DETAIL_URL, 'reference_year': 2016} for i, text in enumerate(_pages(), 1) if needle in re.sub('\\s+', '', text)]
    return {'results': rows[:limit], 'matched_pages': len(rows), 'limit': limit, 'scope': '仅 PDF 文本层；各数据时点、分母及来源不同，参照原文及注释'}
