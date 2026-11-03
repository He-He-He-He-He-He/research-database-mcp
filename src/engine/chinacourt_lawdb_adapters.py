"""中国法院网法律文库公开 HTTP 搜索及全文（站点 HTTPS 证书异常）。"""
import release_runtime
import re
import subprocess
from datetime import date
from urllib.parse import urlencode, urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
BASE = 'http://lawdb.cncourt.org/'

def _fetch(path, params):
    url = BASE + path + '?' + urlencode(params)
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '30', url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('法律文库请求失败: ' + p.stderr.decode('utf-8', 'replace').strip())
    return (url, BeautifulSoup(p.stdout.decode('gb18030', 'replace'), 'html.parser'))

def search(keyword, page=1, mode='title', category='1', start_year=1949, end_year=None):
    """关键词及年份搜索；类别 1 国家、10 地方、30 条约、50 政策、% 全部。"""
    if end_year is None:
        end_year = date.today().year
    if any((isinstance(v, bool) or not (isinstance(v, int) or (isinstance(v, str) and v.isascii() and v.isdigit())) for v in (page, start_year, end_year))):
        raise ValueError('页码和年份须为整数')
    page = int(page)
    start_year = int(start_year)
    end_year = int(end_year)
    category = str(category)
    if not isinstance(keyword, str) or not keyword.strip() or page < 1 or (mode not in ('title', 'content')) or (category not in ('1', '10', '30', '50', '%')) or (not 1901 <= start_year <= end_year <= 2100):
        raise ValueError('关键词、页码、类别、年份或检索范围无效')
    try:
        key = keyword.encode('gb18030')
    except UnicodeEncodeError as exc:
        raise ValueError('关键词无法以网站编码表示') from exc
    url, soup = _fetch('index.php', {'type': category, 'sobj': mode, 'start_year': start_year, 'end_year': end_year, 'action': 'search', 'page': page, 'keywords': key})
    txt = soup.get_text(' ', strip=True)
    match = re.search('第\\s*(\\d+)\\s*页\\s*·\\s*共\\s*(\\d+)\\s*页\\s*·\\s*共\\s*(\\d+)\\s*条', txt)
    if not match:
        if '没有符合条件文件' in txt:
            return {'source': url, 'requested_page': page, 'page': page, 'pages': 0, 'total': 0, 'results': [], 'transport': 'HTTP 明文，需核对权威原文'}
        raise RuntimeError('未识别结果统计，页面可能变化或访问受限')
    rows = []
    for a in soup.select('a.big[href*="show.php?fid="]'):
        fid = parse_qs(urlparse(a.get('href')).query).get('fid', [''])[0]
        if fid.isdigit():
            rows.append({'id': fid, 'title': a.get_text(' ', strip=True), 'url': urljoin(BASE, 'show.php?fid=' + fid)})
    actual_page, pages, total = map(int, match.groups())
    if total > 0 and (not rows):
        raise RuntimeError('上游报告有结果，但未识别本页条目，不能判定为空')
    return {'source': url, 'requested_page': page, 'page': actual_page, 'pages': pages, 'total': total, 'results': rows, 'page_note': '网站将请求页调整为实际页，请以 page 为准' if actual_page != page else None, 'transport': 'HTTP 明文，需核对权威原文'}

def detail(fid):
    if not re.fullmatch('\\d+', str(fid)):
        raise ValueError('fid 须为数字')
    url, soup = _fetch('show.php', {'fid': fid})
    title = soup.select_one('.MTitle')
    metadata = soup.select_one('.STitle')
    if title is None or metadata is None:
        raise RuntimeError('未识别正文，页面可能变化或访问受限')
    td = metadata.find_parent('td')
    return {'source': url, 'title': title.get_text(' ', strip=True), 'metadata': metadata.get_text('\n', strip=True), 'text': td.get_text('\n', strip=True), 'transport': 'HTTP 明文，需核对权威原文'}
