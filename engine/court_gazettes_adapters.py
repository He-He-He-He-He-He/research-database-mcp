"""最高人民法院英文网公报期次目录及 PDF 内容。"""
import release_runtime
from io import BytesIO
import re
import subprocess
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from pypdf import PdfReader
BASE = 'https://english.court.gov.cn/'

def _curl(url):
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '30', '--max-filesize', '15000000', url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('法院公报请求失败: ' + p.stderr.decode('utf-8', 'replace').strip())
    if len(p.stdout) > 15000000:
        raise RuntimeError('文件超过 15 MB')
    return p.stdout

def issues(page=1):
    """读取英文网站公报期次目录；网页结果可链接 PDF 或历史期次网页。"""
    page = int(page)
    if page < 1:
        raise ValueError('页码须大于 0')
    url = BASE + ('gazettes.html' if page == 1 else 'gazettes_' + str(page) + '.html')
    soup = BeautifulSoup(_curl(url), 'html.parser')
    listing = soup.select_one('.List_Div')
    if not listing:
        raise RuntimeError('未识别公报列表，页面可能变更或访问受限')
    results = []
    for e in listing.select('li'):
        a = e.select_one('h4 a')
        d = e.select_one('h6')
        if a:
            raw = a.get('href', '').strip()
            resolved = urljoin(url, raw)
            p = urlparse(resolved)
            valid = bool(raw) and p.scheme in ('http', 'https') and (p.netloc == 'english.court.gov.cn') and (not p.query) and (not p.fragment)
            results.append({'title': a.get_text(' ', strip=True), 'url': raw, 'resolved_url': resolved if valid else None, 'posted': d.get_text(strip=True) if d else None})
    pager = soup.select_one('#displaypagenum')
    return {'source': url, 'page': page, 'pages': int(pager.get('totalcount')) if pager and pager.get('totalcount', '').isdigit() else None, 'results': results, 'note': 'url 保留原始地址，resolved_url 补全相对路径；原站部分地址为 HTTP，不自动改写为 HTTPS，也未验证各链接是否可访问。PDF 可能只有目录。'}

def issues_all(keyword='', limit=30, offset=0):
    if not isinstance(keyword, str):
        raise ValueError('关键词须为字符串')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (limit, offset))) or not 1 <= limit <= 100 or (not 0 <= offset <= 100000):
        raise ValueError('limit 须为 1–100，offset 须为 0–100000')
    first = issues(1)
    pages = first['pages']
    if not isinstance(pages, int) or not 1 <= pages <= 20:
        raise ValueError('来源页数无效或超过上限')
    rows = []
    seen = set()
    for n in range(1, pages + 1):
        r = first if n == 1 else issues(n)
        if r['pages'] != pages or not r['results']:
            raise ValueError('来源页数变化或页面为空')
        for item in r['results']:
            if not item['title'] or not item['resolved_url'] or item['resolved_url'] in seen:
                raise ValueError('来源标题、链接缺失或跨页重复')
            seen.add(item['resolved_url'])
            rows.append(item)
    matches = [item for item in rows if keyword.casefold() in item['title'].casefold()]
    selected = matches[offset:offset + limit]
    return {'source': '最高人民法院英文网公报目录', 'source_pages': pages, 'parsed_items': len(rows), 'keyword': keyword, 'matched_count': len(matches), 'offset': offset, 'limit': limit, 'next_offset': offset + len(selected) if offset + len(selected) < len(matches) else None, 'items': selected, 'note': '逐页读取当前目录并按标题筛选；未提供来源总条数，动态变化可能影响结果，非原子快照。url 为源地址，resolved_url 补全相对链接；HTTP 地址未自动转换或验证，PDF 不一定是完整公报。'}

def pdf_text(url):
    """读取所选官方 PDF 文本，并返回页数；内容可能只是目录，不保证完整公报。"""
    p = urlparse(url)
    if p.scheme != 'https' or p.netloc != 'english.court.gov.cn' or (not re.fullmatch('/pdf/[^/]+\\.pdf', p.path, re.I)):
        raise ValueError('仅接受法院英文站的 PDF 链接')
    raw = _curl(url)
    if not raw.startswith(b'%PDF'):
        raise RuntimeError('返回内容不是 PDF')
    doc = PdfReader(BytesIO(raw))
    return {'source': url, 'pages': len(doc.pages), 'text_by_page': [page.extract_text() or '' for page in doc.pages]}
