"""国家药品监督管理局 2023 年监管统计报告：PDF 文本与候选表格。"""
import release_runtime
import contextlib, io, re
from urllib.parse import urljoin, urlsplit
import fitz
from nmpa_annual_statistics_2025_tables_adapter import _get
LANDING = 'https://www.nmpaic.org.cn/yjzxyw/202505/t20250516_427148.html'

def source():
    html = _get(LANDING, 1000000).decode('utf-8')
    titles = re.findall('var\\s+title\\s*=\\s*[\'\\"]([^\'\\"]+)[\'\\"]', html)
    hrefs = re.findall('var\\s+href\\s*=\\s*[\'\\"]([^\'\\"]+)[\'\\"]', html)
    if titles != ['药品监督管理统计年度数据（2023年）.pdf'] or len(hrefs) != 1:
        raise ValueError('官方页面附件结构变化')
    u = urljoin(LANDING, hrefs[0])
    p = urlsplit(u)
    if p.scheme != 'https' or p.netloc != 'www.nmpaic.org.cn' or (not re.fullmatch('/yjzxyw/202505/P\\d+\\.pdf', p.path)) or p.query or p.fragment:
        raise ValueError('非预期附件路径')
    return {'landing_url': LANDING, 'pdf_url': u, 'title': titles[0], 'year': 2023, 'publisher': '国家药监局综合和规划财务司、信息中心'}

def _document():
    meta = source()
    raw = _get(meta['pdf_url'], 10000000)
    if not raw.startswith(b'%PDF-'):
        raise ValueError('附件不是 PDF')
    d = fitz.open(stream=raw, filetype='pdf')
    if len(d) > 200:
        raise ValueError('异常页数')
    return (meta, d)

def page(page_number):
    if type(page_number) is not int or page_number < 1:
        raise ValueError('页码必须为正整数')
    m, d = _document()
    if page_number > len(d):
        raise ValueError('页码超出范围')
    p = d[page_number - 1]
    with contextlib.redirect_stdout(io.StringIO()):
        tables = p.find_tables().tables
    return {**m, 'total_pdf_pages': len(d), 'physical_page': page_number, 'text': p.get_text(), 'candidate_tables': [t.extract() for t in tables], 'note': '候选表可能漏数、拆列或错列；必须核对原 PDF 的表头、注释、单位和口径，物理页码与印刷页码不同。'}

def search(keyword):
    if not isinstance(keyword, str) or not keyword.strip():
        raise ValueError('关键词不能为空')
    m, d = _document()
    needle = re.sub('\\s+', '', keyword)
    out = []
    for i, p in enumerate(d):
        text = p.get_text()
        if needle in re.sub('\\s+', '', text):
            out.append({'physical_page': i + 1, 'text': text})
    return {**m, 'total_pdf_pages': len(d), 'keyword': keyword, 'matches': out, 'note': '文字提取，不包括图像文字；命中可能包括目录页。应核对原文及口径。'}
