"""科技部图文播报目录与完整文字实录。"""
import release_runtime
import re, subprocess
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
BASE = 'https://www.most.gov.cn/xwzx/twzb/'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.most.gov.cn' or (not p.path.startswith('/xwzx/twzb/')) or p.query or p.fragment:
        raise ValueError('仅支持科技部图文播报 HTTPS 地址')
    return release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '25', '--max-redirs', '0', url], check=True, capture_output=True).stdout.decode('utf-8-sig')

class _Index(HTMLParser):

    def __init__(self):
        super().__init__()
        self.title = False
        self.row = None
        self.rows = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'h1':
            self.title = True
        elif self.title and tag == 'a' and a.get('href', '').startswith('/xwzx/twzb/'):
            self.row = {'title': a.get('title', '').strip(), 'url': urljoin(BASE, a['href'])}
        elif self.row is not None and tag == 'span' and a.get('data-txt'):
            self.row['time'] = a['data-txt']
            self.rows.append(self.row)
            self.row = None

    def handle_endtag(self, tag):
        if tag == 'h1':
            self.title = False

class _Links(HTMLParser):

    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'a' and 'twzbwzsl/' in a.get('href', ''):
            self.urls.append(a['href'].strip())

class _Text(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.found = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if self.depth and tag not in ('br', 'img', 'hr', 'input', 'meta', 'link'):
            self.depth += 1
        elif not self.depth and tag == 'div' and any((c in dict(attrs).get('class', '').split() for c in ('trs_editor_view', 'TRS_Editor'))):
            self.depth = 1
            self.found = True
        if self.depth and tag in ('p', 'div', 'br'):
            self.parts.append('\n')

    def handle_startendtag(self, tag, attrs):
        if self.depth and tag == 'br':
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if self.depth and tag not in ('br', 'img', 'hr', 'input', 'meta', 'link'):
            self.depth -= 1

    def handle_data(self, data):
        if self.depth:
            self.parts.append(data)

def most_press_list(page=1, keyword=''):
    page = int(page)
    if page < 1 or page > 200:
        raise ValueError('页码必须在 1—200')
    url = BASE if page == 1 else urljoin(BASE, f'index_{page - 1}.html')
    p = _Index()
    p.feed(_get(url))
    needle = ''.join(keyword.split()).casefold()
    if not p.rows:
        raise ValueError('未找到目录记录或页面结构变更')
    return [r for r in p.rows if needle in ''.join((''.join(str(v).split()) for v in r.values())).casefold()]

def most_press_detail(url):
    p = urlparse(url)
    if not re.fullmatch('/xwzx/twzb/[A-Za-z0-9_]+/(?:index\\.html)?', p.path):
        raise ValueError('仅支持科技部发布会专题主页')
    links = _Links()
    links.feed(_get(url))
    urls = list(dict.fromkeys((urljoin(url, x) for x in links.urls)))
    if not urls:
        return {'url': url, 'transcript_url': None, 'text': None, 'note': '未发现文字实录链接'}
    target = urls[0]
    _get_url = urlparse(target)
    if _get_url.hostname != 'www.most.gov.cn' or '/twzbwzsl/' not in _get_url.path:
        raise ValueError('文字实录链接不在预期栏目')
    body = _Text()
    body.feed(_get(target))
    if not body.found:
        raise ValueError('未找到文字实录正文')
    return {'url': url, 'transcript_url': target, 'text': '\n'.join((x.strip() for x in ''.join(body.parts).splitlines() if x.strip()))}
