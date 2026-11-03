"""广电总局公告分页及影视备案、发行许可通告。"""
import release_runtime
import re, subprocess, xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import urlencode, urljoin, urlparse
BASE = 'https://www.nrta.gov.cn'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.nrta.gov.cn':
        raise ValueError('只读取国家广播电视总局 HTTPS 资源')
    return release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '30', '--max-redirs', '0', url], check=True, capture_output=True).stdout.decode('utf-8-sig')

class _Entry(HTMLParser):

    def __init__(self):
        super().__init__()
        self.title = ''
        self.url = ''
        self.date = ''
        self.span = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'a' and a.get('title'):
            self.title = a['title']
            self.url = a.get('href', '')
        elif tag == 'span':
            self.span = True

    def handle_data(self, data):
        if self.span:
            self.date += data

    def handle_endtag(self, tag):
        if tag == 'span':
            self.span = False

class _Body(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.found = False
        self.parts = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if self.depth and tag == 'div':
            self.depth += 1
        elif not self.depth and tag == 'div' and (a.get('id') == 'zoom'):
            self.depth = 1
            self.found = True
        if self.depth and tag in ('p', 'div', 'br', 'tr'):
            self.parts.append('\n')
        if self.depth and tag in ('td', 'th'):
            self.parts.append('\t')
        if self.depth and tag == 'a' and a.get('href'):
            self.links.append(a['href'])

    def handle_data(self, data):
        if self.depth:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if self.depth and tag == 'div':
            self.depth -= 1

def nrta_permit_announcements(page=1, keyword=''):
    page = int(page)
    if page < 1 or page > 500:
        raise ValueError('页码必须在 1—500')
    q = urlencode({'page': page, 'webid': 1, 'path': BASE + '/', 'columnid': 113, 'unitid': 14416, 'permissiontype': 0})
    url = BASE + '/module/web/jpage/dataproxy.jsp?' + q
    root = ET.fromstring(_get(url))
    total = int(root.findtext('totalrecord'))
    pages = int(root.findtext('totalpage'))
    rows = []
    if page > pages:
        raise ValueError(f'页码超出当前总页数 {pages}')
    for el in root.findall('./recordset/record'):
        p = _Entry()
        p.feed(el.text or '')
        if p.title and p.url:
            rows.append({'title': p.title, 'url': p.url, 'date': p.date.strip()})
    if not rows:
        raise ValueError('未解析到公告，页面结构可能变化')
    needle = ''.join(keyword.split()).casefold()
    return {'page': page, 'pages': pages, 'total': total, 'items': [r for r in rows if needle in ''.join((''.join(v.split()) for v in r.values())).casefold()]}

def nrta_permit_announcement_detail(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.nrta.gov.cn' or (not re.fullmatch('/art/\\d{4}/\\d{1,2}/\\d{1,2}/art_113_\\d+\\.html', p.path)) or p.query or p.fragment:
        raise ValueError('仅支持广电总局公告公示详情地址')
    body = _Body()
    body.feed(_get(url))
    if not body.found:
        raise ValueError('未找到公告正文')
    links = []
    for value in body.links:
        link = urljoin(url, value)
        q = urlparse(link)
        if q.scheme == 'https' and q.hostname == 'www.nrta.gov.cn' and (q.path.startswith('/module/download/') or q.path.lower().endswith(('.pdf', '.xls', '.xlsx', '.doc', '.docx'))):
            links.append(link)
    return {'url': url, 'text': '\n'.join((x.strip() for x in ''.join(body.parts).splitlines() if x.strip())), 'attachments': list(dict.fromkeys(links))}
