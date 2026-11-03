"""财政部中央政府收支及融资、季度债务余额公开原表。"""
import release_runtime
import contextlib, io, re
from urllib.parse import urljoin, urlsplit
import requests, fitz
from bs4 import BeautifulSoup
BASE = 'https://gks.mof.gov.cn/tongjishuju/'

def _get(url):
    r = requests.get(url, timeout=25, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect or len(r.content) > 12000000:
        raise ValueError('响应跳转或过大')
    return r.content

def catalog(page=1):
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 100):
        raise ValueError('页码应为1–100')
    u = BASE + ('' if page == 1 else f'index_{page - 1}.htm')
    s = BeautifulSoup(_get(u), 'html.parser')
    items = []
    for a in s.select('a[href][title]'):
        title = a['title'].strip()
        link = urljoin(u, a['href'])
        p = urlsplit(link)
        if '中央政府收支' in title and p.scheme == 'https' and (p.hostname == 'gks.mof.gov.cn') and re.fullmatch('/tongjishuju/\\d{6}/P\\d+\\.pdf', p.path):
            items.append({'title': title, 'url': link})
    return {'source': '财政部国库司统计数据栏目', 'page': page, 'source_url': u, 'items': items, 'note': '仅筛当前栏目页的中央政府收支原表，栏目中有其他资料；无匹配不代表该期未发布。'}

def report(url):
    if not isinstance(url, str):
        raise ValueError('必须提供链接')
    p = urlsplit(url)
    if p.scheme != 'https' or p.hostname != 'gks.mof.gov.cn' or p.query or p.fragment or (not re.fullmatch('/tongjishuju/\\d{6}/P\\d+\\.pdf', p.path)):
        raise ValueError('仅接受财政部国库司栏目中的 PDF')
    b = _get(url)
    if not b.startswith(b'%PDF-'):
        raise ValueError('响应不是 PDF')
    doc = fitz.open(stream=b, filetype='pdf')
    if len(doc) > 50:
        raise ValueError('PDF 页数过多')
    pages = []
    for page in doc:
        with contextlib.redirect_stdout(io.StringIO()):
            tables = [t.extract() for t in page.find_tables().tables]
        pages.append({'page': page.number + 1, 'text': page.get_text(), 'tables': tables})
    return {'source': '财政部国库司', 'source_url': url, 'pages': pages, 'note': '原 PDF 表格自动识别，可能存在跨格误差；单位、时段、注释、月度流量与季度债务存量以原表为准，空单元格不等于零。'}
