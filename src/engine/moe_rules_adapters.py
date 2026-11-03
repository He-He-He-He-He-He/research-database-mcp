"""教育部规章公开目录与正文。"""
import release_runtime
import re
import subprocess
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from szse_chinext_adapters import _Links
BASE = 'https://www.moe.gov.cn/jyb_xxgk/xxgk/zhengce/guizhang/'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.moe.gov.cn' or (not p.path.startswith('/jyb_xxgk/xxgk/zhengce/guizhang/')) or p.query or p.fragment:
        raise ValueError('仅允许教育部规章栏目')
    return release_runtime.run(['curl', '--location', '--max-redirs', '3', '--proto-redir', '=http,https', '--compressed', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout.decode('utf-8')

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
            elif 'TRS_Editor' in dict(attrs).get('class', '').split():
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

def education_rules(page=1, keyword=''):
    page = int(page)
    if not 1 <= page <= 100:
        raise ValueError('页码超出范围')
    p = _Links()
    p.feed(_get(BASE if page == 1 else urljoin(BASE, f'index_{page - 1}.html')))
    out = []
    for href, title in p.links:
        u = urljoin(BASE, href)
        if re.fullmatch(re.escape(BASE) + '\\d{6}/t\\d{8}_\\d+\\.html', u) and keyword in title:
            out.append({'title': title, 'url': u})
    if not out and (not keyword):
        raise ValueError('未找到规章目录')
    return out

def education_rule_detail(url):
    p = _Body()
    p.feed(_get(url))
    text = '\n'.join((s.strip() for s in ''.join(p.parts).splitlines() if s.strip()))
    if len(text) < 100:
        raise ValueError('未识别规章正文')
    return {'url': url, 'text': text, 'note': '教育部规章正文；施行和后续修改以官方公告为准。'}
