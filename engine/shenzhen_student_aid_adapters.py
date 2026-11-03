"""深圳市教育局学生资助政策与资讯公开栏目。"""
import release_runtime
import re
import subprocess
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from szse_chinext_adapters import _Links
BASE = 'https://szeb.sz.gov.cn/home/zdyw/xszz/xszz_zcwj/'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'szeb.sz.gov.cn' or (not p.path.startswith('/home/zdyw/xszz/xszz_zcwj/')) or p.query or p.fragment:
        raise ValueError('仅允许深圳教育学生资助栏目')
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
            elif 'news_cont_d_wrap' in dict(attrs).get('class', '').split():
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

def student_aid_list(keyword=''):
    p = _Links()
    p.feed(_get(BASE + 'index.html'))
    out = []
    for href, title in p.links:
        url = urljoin(BASE, href)
        if re.fullmatch(re.escape(BASE) + 'content/post_\\d+\\.html', url) and title and (keyword in title):
            out.append({'title': title, 'url': url})
    return out

def student_aid_detail(url):
    p = _Body()
    p.feed(_get(url))
    text = '\n'.join((s.strip() for s in ''.join(p.parts).splitlines() if s.strip()))
    if len(text) < 100:
        raise ValueError('未识别正文')
    return {'url': url, 'text': text, 'note': '深圳市教育局资助栏目，包含国家与地方信息；受众、适用年度、效力和附件以原页为准。'}
