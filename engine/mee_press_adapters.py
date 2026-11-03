"""生态环境部新闻发布栏目目录与原文。"""
import release_runtime
import re, subprocess
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
BASE = 'https://www.mee.gov.cn/ywdt/xwfb/'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.mee.gov.cn' or (not p.path.startswith('/ywdt/xwfb/')) or p.query or p.fragment:
        raise ValueError('仅支持生态环境部新闻发布栏目 HTTPS 地址')
    return release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '25', '--max-redirs', '0', url], check=True, capture_output=True).stdout.decode('utf-8-sig')

class _Index(HTMLParser):

    def __init__(self):
        super().__init__()
        self.row = None
        self.capture = None
        self.rows = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'dt':
            self.row = {}
        elif self.row is not None and tag == 'a' and ('cjcx_biaobnan' in a.get('class', '').split()):
            self.row['url'] = urljoin(BASE, a.get('href', ''))
            self.row['title'] = ''
            self.capture = 'title'
        elif self.row is not None and tag == 'span' and ('cjcx_shijian' in a.get('class', '').split()):
            self.row['date'] = ''
            self.capture = 'date'

    def handle_data(self, data):
        if self.row is not None and self.capture:
            self.row[self.capture] += data

    def handle_endtag(self, tag):
        if tag in ('a', 'span'):
            self.capture = None
        elif tag == 'dt' and self.row is not None:
            if all((self.row.get(x) for x in ('url', 'title', 'date'))):
                self.rows.append({k: v.strip() for k, v in self.row.items()})
            self.row = None

class _Body(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.found = False
        self.text = []

    def handle_starttag(self, tag, attrs):
        if self.depth and tag not in ('br', 'img', 'input', 'hr', 'meta', 'link'):
            self.depth += 1
        elif not self.depth and tag == 'div' and ('neiright_JPZ_GK_CP' in dict(attrs).get('class', '').split()):
            self.depth = 1
            self.found = True
        if self.depth and tag in ('p', 'div', 'br'):
            self.text.append('\n')

    def handle_startendtag(self, tag, attrs):
        if self.depth and tag == 'br':
            self.text.append('\n')

    def handle_endtag(self, tag):
        if self.depth and tag not in ('br', 'img', 'input', 'hr', 'meta', 'link'):
            self.depth -= 1

    def handle_data(self, data):
        if self.depth:
            self.text.append(data)

def mee_press_list(page=1, keyword=''):
    page = int(page)
    if page < 1 or page > 500:
        raise ValueError('页码必须在 1—500')
    url = BASE if page == 1 else urljoin(BASE, f'index_{page - 1}.shtml')
    p = _Index()
    p.feed(_get(url))
    needle = ''.join(keyword.split()).casefold()
    if not p.rows:
        raise ValueError('栏目无条目或页面结构已改变')
    return [r for r in p.rows if needle in ''.join((''.join(str(v).split()) for v in r.values())).casefold()]

def mee_press_detail(url):
    p = urlparse(url)
    if not re.fullmatch('/ywdt/xwfb/\\d{6}/t\\d{8}_\\d+\\.shtml', p.path):
        raise ValueError('仅支持新闻发布栏目文章详情')
    body = _Body()
    body.feed(_get(url))
    if not body.found:
        raise ValueError('未找到正文，页面结构可能变化')
    text = '\n'.join((x.strip() for x in ''.join(body.text).splitlines() if x.strip()))
    return {'url': url, 'text': text, 'note': '生态环境部新闻发布栏目原文；图片文字、附件不自动解析。'}
