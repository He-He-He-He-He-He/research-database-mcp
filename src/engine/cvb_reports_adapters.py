"""中国视听大数据公开专题报告和数据发布。"""
import release_runtime
import subprocess
from io import BytesIO
from urllib.parse import quote, urlparse
from pypdf import PdfReader
from cvb_rankings_adapters import _get
HOST = 'https://www.cavbd.cn/prod-api'

def reports(kind='专题报告', page=1, size=8):
    page, size = (int(page), int(size))
    if kind not in ('专题报告', '数据发布') or page < 1 or (not 1 <= size <= 100):
        raise ValueError('类别、页码或每页数量无效')
    return _get('reports/list2', {'type': kind, 'pageNum': page, 'pageSize': size})

def report_pdf(path):
    """按列表返回的官网 PDF 路径读取原文并逐页提取文字。"""
    p = urlparse(path)
    if p.scheme or p.netloc or p.query or p.fragment or (not p.path.startswith('/profile/upload/')) or ('..' in p.path.split('/')) or (not p.path.lower().endswith('.pdf')):
        raise ValueError('仅接受报告列表返回的站内 PDF 路径')
    url = HOST + quote(p.path, safe='/')
    r = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '30', '--max-filesize', '15000000', url], capture_output=True, timeout=35)
    if r.returncode:
        raise RuntimeError('PDF 请求失败: ' + r.stderr.decode('utf-8', 'replace').strip())
    if len(r.stdout) > 15000000 or not r.stdout.startswith(b'%PDF'):
        raise RuntimeError('附件超限或非 PDF')
    doc = PdfReader(BytesIO(r.stdout))
    return {'source': url, 'pages': len(doc.pages), 'text_by_page': [p.extract_text() or '' for p in doc.pages]}
