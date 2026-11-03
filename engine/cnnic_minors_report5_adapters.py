"""第五次全国未成年人互联网使用情况调查报告 PDF 查询。"""
import release_runtime
from functools import lru_cache
from pathlib import Path
import re
PDF_PATH = Path(__file__).with_name('第五次全国未成年人互联网使用情况调查报告.pdf')
SOURCE_URL = 'https://www.cnnic.cn/NMediaFile/2023/1225/MAIN1703484375296SPBHV29S0V.pdf'
DETAIL_URL = 'https://www.cnnic.cn/n4/2023/1225/c116-10908.html'

@lru_cache(maxsize=1)
def _pages():
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError('需要安装可选依赖 pypdf') from e
    reader = PdfReader(str(PDF_PATH))
    if len(reader.pages) != 64:
        raise ValueError('PDF 页数异常')
    return tuple((page.extract_text() or '' for page in reader.pages))

def search_cnnic_minors_report5(keyword, limit=20):
    """搜索原报告 PDF 文本，返回命中页和原文。"""
    needle = re.sub('\\s+', '', keyword)
    if not needle:
        raise ValueError('请输入关键词')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 64):
        raise ValueError('limit 应为 1 至 64 的整数')
    rows = [{'pdf_page': i, 'text': text, 'source_url': SOURCE_URL, 'detail_url': DETAIL_URL, 'publication_year': 2023} for i, text in enumerate(_pages(), 1) if needle in re.sub('\\s+', '', text)]
    return {'results': rows[:limit], 'matched_pages': len(rows), 'limit': limit, 'scope': '仅 PDF 文本层；原报告包含多年份数据，应核查具体指标的时点、范围和脚注'}
