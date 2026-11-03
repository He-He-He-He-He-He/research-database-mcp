"""国家数据局信息公开其他政策栏目。"""
import release_runtime
import re
import subprocess
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
BASE = 'https://www.nda.gov.cn/sjj/xxgk/gknr/qtzc/'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.nda.gov.cn' or (not p.path.startswith('/sjj/xxgk/gknr/qtzc/')) or p.query or p.fragment:
        raise ValueError('仅允许国家数据局其他政策栏目')
    return release_runtime.run(['curl', '--compressed', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout.decode('utf-8')

class _Rows(HTMLParser):

    def __init__(self):
        super().__init__()
        self.row = None
        self.rows = []

    def handle_starttag(self, t, attrs):
        if t == 'tr':
            self.row = {'href': '', 'parts': []}
        elif t == 'a' and self.row is not None:
            self.row['href'] = dict(attrs).get('href', '')

    def handle_data(self, s):
        if self.row is not None:
            self.row['parts'].append(s)

    def handle_endtag(self, t):
        if t == 'tr' and self.row is not None:
            self.rows.append(self.row)
            self.row = None

class _Body(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.skip = 0
        self.parts = []

    def handle_starttag(self, t, attrs):
        if t == 'div':
            if self.depth:
                self.depth += 1
            elif 'article' in dict(attrs).get('class', '').split():
                self.depth = 1
        if self.depth and t in ('style', 'script'):
            self.skip += 1
        if self.depth and (not self.skip) and (t in ('p', 'br', 'h1', 'h2')):
            self.parts.append('\n')

    def handle_data(self, s):
        if self.depth and (not self.skip):
            self.parts.append(s)

    def handle_endtag(self, t):
        if self.depth and t in ('style', 'script') and self.skip:
            self.skip -= 1
        if t == 'div' and self.depth:
            self.depth -= 1

def nda_policy_list(page=1, keyword=''):
    page = int(page)
    if not 1 <= page <= 100:
        raise ValueError('页码超出范围')
    p = _Rows()
    p.feed(_get(urljoin(BASE, f'list/index_pc_{page}.html')))
    out = []
    for row in p.rows:
        u = urljoin(BASE, row['href'])
        m = re.search("name\\s*:\\s*'公开事项名称'\\s*,\\s*value\\s*:\\s*'([^']+)'", ''.join(row['parts']))
        if m and re.fullmatch(re.escape(BASE) + '\\d{4}/\\d+_pc\\.html', u) and (keyword in m.group(1)):
            out.append({'title': m.group(1), 'url': u})
    if not out and (not keyword):
        raise ValueError('未找到政策目录')
    return out

def nda_policy_detail(url):
    p = _Body()
    p.feed(_get(url))
    text = '\n'.join((s.strip() for s in ''.join(p.parts).splitlines() if s.strip()))
    if len(text) < 100:
        raise ValueError('未识别正文')
    return {'url': url, 'text': text, 'note': '国家数据局信息公开的其他政策正文；适用范围、有效性及附件请核对原文。'}
