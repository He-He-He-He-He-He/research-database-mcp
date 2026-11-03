"""人社部主要统计数据：湖北省人社厅转载目录与 PDF 原表。"""
import release_runtime
import contextlib, io, re, subprocess
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup
import fitz
BASE = 'https://rst.hubei.gov.cn/zfxxgk/fdzdgknr/tjxx/'
PATHS = {2024: '2024', 2025: '2025', 2026: '2026_tjxx'}

def _get(url, max_bytes=10000000):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', '--max-filesize', str(max_bytes), url], capture_output=True, timeout=30)
    if p.returncode or len(p.stdout) > max_bytes:
        raise ValueError('网站请求失败或文件过大')
    return p.stdout

def _safe(url, suffix):
    p = urlsplit(url)
    return p.scheme == 'https' and p.hostname == 'rst.hubei.gov.cn' and (not p.query) and (not p.fragment) and re.fullmatch('/zfxxgk/fdzdgknr/tjxx/[A-Za-z0-9_/.-]+\\.' + suffix, p.path)

def catalog(year, page=1):
    if year not in PATHS or isinstance(page, bool) or (not isinstance(page, int)) or (not 1 <= page <= 10):
        raise ValueError('支持 2024–2026，页码 1–10')
    url = BASE + PATHS[year] + '/' + ('' if page == 1 else f'index_{page - 1}.shtml')
    soup = BeautifulSoup(_get(url), 'html.parser')
    items = []
    for a in soup.select('a[href]'):
        title = a.get_text(' ', strip=True)
        if '人力资源和社会保障主要统计' not in title or not re.search('20\\d\\d年1[-—至]', title):
            continue
        u = urljoin(url, a['href']).replace('http://rst.hubei.gov.cn/', 'https://rst.hubei.gov.cn/', 1)
        if _safe(u, 'shtml'):
            items.append({'title': title, 'url': u})
    return {'source': '人社部主要统计数据（湖北省人社厅转载目录）', 'year': year, 'page': page, 'source_url': url, 'items': items, 'note': '仅列本页转载的全国统计快报，不是完整历史；累计数和时点数需查原文，非湖北省本地数据。'}

def report(url):
    if not isinstance(url, str) or not _safe(url, 'shtml'):
        raise ValueError('仅接受湖北省人社厅统计栏目官方详情链接')
    s = BeautifulSoup(_get(url), 'html.parser')
    title = s.select_one('h2')
    pdfs = []
    for a in s.select('a[href]'):
        u = urljoin(url, a['href']).replace('http://rst.hubei.gov.cn/', 'https://rst.hubei.gov.cn/', 1)
        if _safe(u, 'pdf') and u not in pdfs:
            pdfs.append(u)
    if len(pdfs) != 1:
        raise ValueError('未识别唯一官方 PDF，需人工查看详情页')
    raw = _get(pdfs[0])
    if not raw.startswith(b'%PDF-'):
        raise ValueError('附件不是 PDF')
    d = fitz.open(stream=raw, filetype='pdf')
    if len(d) > 50:
        raise ValueError('PDF 页数过多')
    pages = []
    for page in d:
        tables = []
        with contextlib.redirect_stdout(io.StringIO()):
            for table in page.find_tables().tables:
                tables.append(table.extract())
        pages.append({'page': page.number + 1, 'text': page.get_text(), 'tables': tables})
    return {'source': '人社部主要统计数据（湖北省人社厅转载）', 'title': title.get_text(' ', strip=True) if title else None, 'source_url': url, 'pdf_url': pdfs[0], 'pages': pages, 'note': 'PDF 自动提取表格可能有跨行或跨页误差；数量和单位以官方原 PDF 为准。指标有累计值及期末值，勿简单相加，核对附注和统计口径。'}
