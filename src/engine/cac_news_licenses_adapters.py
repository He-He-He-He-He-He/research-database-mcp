"""国家网信办互联网新闻服务许可：最新公告及中央网站名单。"""
import release_runtime
import re, subprocess, hashlib
from io import BytesIO
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from pypdf import PdfReader
INDEX = 'https://www.cac.gov.cn/hdfw/hlwxwxxfw/A093809index_1.htm'
HOST = 'https://www.cac.gov.cn'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.cac.gov.cn':
        raise ValueError('仅接受国家网信办 HTTPS 来源')
    r = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '30', '--max-filesize', '15000000', url], capture_output=True, timeout=35)
    if r.returncode:
        raise RuntimeError('网信办请求失败: ' + r.stderr.decode('utf8', 'replace').strip())
    if len(r.stdout) > 15000000:
        raise RuntimeError('内容超过 15 MB')
    return r.stdout

def latest():
    soup = BeautifulSoup(_get(INDEX), 'html.parser')
    matches = [urljoin(INDEX, a['href']) for a in soup.find_all('a', href=True) if a.get_text(' ', strip=True) == '互联网新闻信息服务单位许可信息']
    if len(matches) != 1:
        raise RuntimeError('未识别唯一最新许可公告')
    page = matches[0]
    s = BeautifulSoup(_get(page), 'html.parser')
    b = s.select_one('#BodyLabel')
    if b is None:
        raise RuntimeError('未识别公告正文')
    links = [{'label': a.get_text(' ', strip=True), 'url': urljoin(page, a['href'])} for a in b.find_all('a', href=True)]
    return {'index': INDEX, 'source': page, 'text': b.get_text(' ', strip=True), 'links': links}

def central_websites(keyword=''):
    """最新公告首个中央单位网站表，保留 PDF 每行原文、页码和序号。"""
    info = latest()
    matches = [x for x in info['links'] if x['label'] == '互联网站' and urlparse(x['url']).hostname == 'www.cac.gov.cn']
    if len(matches) < 2:
        raise RuntimeError('未识别中央与其他单位网站分类')
    detail = matches[0]['url']
    s = BeautifulSoup(_get(detail), 'html.parser')
    b = s.select_one('#BodyLabel')
    if b is None:
        raise RuntimeError('未识别名单详情')
    html = str(b)
    pdfs = re.findall('(?:(?:https?:)?//www\\.cac\\.gov\\.cn)?(/rootimages/uploadimg/[^"\\s?]+?\\.pdf)', html)
    pdfs = list(dict.fromkeys(pdfs))
    if len(pdfs) != 1:
        raise RuntimeError('未识别唯一名单 PDF')
    url = HOST + pdfs[0]
    raw = _get(url)
    if not raw.startswith(b'%PDF'):
        raise RuntimeError('名单不是 PDF')
    pdf = PdfReader(BytesIO(raw))
    rows = []
    expected = None
    for i, page in enumerate(pdf.pages, 1):
        text = page.extract_text() or ''
        if i == 1:
            m = re.search('名单（共(\\d+)个）', text)
            if not m:
                raise RuntimeError('未识别名单官方数量')
            expected = int(m.group(1))
        for line in text.splitlines():
            line = line.strip()
            m = re.match('^(\\d{1,5})\\s+(.+)$', line)
            if m and int(m.group(1)) == len(rows) + 1:
                rows.append({'number': int(m.group(1)), 'page': i, 'raw_text': m.group(2)})
            elif rows and line:
                rows[-1]['raw_text'] += ' ' + line
    if len(rows) != expected:
        raise RuntimeError(f'名单行数 {len(rows)} 不等于公告数 {expected}，拒绝返回不完整解析')
    return {'announcement': info['source'], 'detail': detail, 'pdf': url, 'sha256': hashlib.sha256(raw).hexdigest(), 'expected': expected, 'matching': sum((keyword in x['raw_text'] for x in rows)), 'rows': [x for x in rows if keyword in x['raw_text']]}
