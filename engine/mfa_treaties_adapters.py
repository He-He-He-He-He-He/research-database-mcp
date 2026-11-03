"""外交部中华人民共和国条约数据库公开检索。"""
import release_runtime
import re
import subprocess
from urllib.parse import urlencode, urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
BASE = 'https://treaty.mfa.gov.cn/web/'

def _fetch(path, params):
    url = BASE + path + '?' + urlencode(params)
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '30', url], capture_output=True, text=True, timeout=35)
    if p.returncode:
        raise RuntimeError('条约数据库请求失败: ' + p.stderr.strip())
    return (url, BeautifulSoup(p.stdout, 'html.parser'))

def search(keyword, page=1, kind='all'):
    """按关键词分页搜索，kind 为 all/1(多边)/2(双边)。"""
    page = int(page)
    kind = str(kind)
    if not keyword or not keyword.strip() or page < 1 or (kind not in ('all', '1', '2')):
        raise ValueError('请填写关键词、正页码和有效类别')
    url, soup = _fetch('list.jsp', {'keywords': keyword, 'chnltype_c': kind, 'nPageIndex_': page})
    listing = soup.select_one('ul.neirong_ul')
    if listing is None:
        raise RuntimeError('未识别结果页，网站可能变更或限制访问')
    rows = []
    for li in listing.find_all('li', recursive=False):
        a = li.find('a', href=True)
        cells = li.find_all('div', recursive=False)
        if a is None or len(cells) < 5:
            continue
        rows.append({'title': a.get_text(' ', strip=True), 'url': urljoin(BASE, a['href']), 'type': cells[1].get_text(' ', strip=True), 'subject': cells[2].get_text(' ', strip=True), 'china_signed': cells[3].get_text(' ', strip=True) or None, 'treaty_effective': cells[4].get_text(' ', strip=True) or None})
    last = soup.select('.page a')
    pages = None
    for a in last:
        if a.get_text(strip=True) == '尾页':
            try:
                pages = int(parse_qs(urlparse(a.get('href', '')).query)['nPageIndex_'][0])
            except (KeyError, ValueError):
                pass
    return {'source': url, 'page': page, 'pages': pages, 'results': rows}

def detail(url):
    """读取搜索结果链接的详情表及文本链接；允许官方条约库的 detail 页面。"""
    u = urlparse(url)
    if u.scheme != 'https' or u.netloc != 'treaty.mfa.gov.cn' or (not re.fullmatch('/web/detail\\d*\\.jsp', u.path)):
        raise ValueError('只接受条约库官方 detail 页面 URL')
    obj = parse_qs(u.query).get('objid', [''])[0]
    if not re.fullmatch('\\d+', obj):
        raise ValueError('条约 objid 无效')
    source, soup = _fetch(u.path.rsplit('/', 1)[-1], {'objid': obj})
    title = soup.select_one('.neirongp')
    table = soup.select_one('table.tab_con_a')
    if title is None or table is None:
        raise RuntimeError('未识别详情表，网站可能变更或限制访问')
    rows = [[td.get_text(' ', strip=True) for td in tr.find_all('td', recursive=False)] for tr in table.find_all('tr')]
    links = [{'label': a.parent.get_text(' ', strip=True), 'url': urljoin(source, a['href'])} for a in table.select('a[href]')]
    return {'source': source, 'title': title.get_text(' ', strip=True), 'table_rows': rows, 'text_links': links}
