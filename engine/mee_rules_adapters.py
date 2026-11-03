"""生态环境部规章库公开目录及正文。"""
import release_runtime
import re
import subprocess
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from szse_chinext_adapters import _Links
BASE = 'https://www.mee.gov.cn/gzk/gz/'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.mee.gov.cn' or (not p.path.startswith('/gzk/gz/')) or p.query or p.fragment:
        raise ValueError('仅允许生态环境部规章栏目')
    return release_runtime.run(['curl', '--compressed', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout.decode('utf-8')

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
            elif 'gz_content' in dict(attrs).get('class', '').split():
                self.depth = 1
        if self.depth and t in ('style', 'script'):
            self.skip += 1
        if self.depth and (not self.skip) and (t in ('p', 'br', 'h1', 'h2', 'h3')):
            self.parts.append('\n')

    def handle_data(self, s):
        if self.depth and (not self.skip):
            self.parts.append(s)

    def handle_endtag(self, t):
        if self.depth and t in ('style', 'script') and self.skip:
            self.skip -= 1
        if t == 'div' and self.depth:
            self.depth -= 1

def mee_rules(page=1, keyword=''):
    page = int(page)
    if not 1 <= page <= 100:
        raise ValueError('页码超出范围')
    url = BASE if page == 1 else urljoin(BASE, f'index_{page - 1}.shtml')
    p = _Links()
    p.feed(_get(url))
    out = []
    for href, title in p.links:
        u = urljoin(BASE, href)
        if re.fullmatch(re.escape(BASE) + '\\d{6}/t\\d{8}_\\d+\\.shtml', u) and keyword in title:
            out.append({'title': title, 'url': u})
    if not out and (not keyword):
        raise ValueError('未找到规章条目')
    return out

def mee_rule_detail(url):
    p = _Body()
    p.feed(_get(url))
    text = '\n'.join((s.strip() for s in ''.join(p.parts).splitlines() if s.strip()))
    if len(text) < 100:
        raise ValueError('未识别规章正文')
    return {'url': url, 'text': text, 'note': '生态环境部公开规章文字；修改、施行和现行效力请核对官方页面及后续公告。'}
