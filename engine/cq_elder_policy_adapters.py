"""重庆市民政局汇集的国家级养老政策目录。"""
import release_runtime
import re
import subprocess
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from szse_chinext_adapters import _Links
BASE = 'https://mzj.cq.gov.cn/zwgk_218/fdzdgknr/zdlyxxgk/lnrfl/ylfwzcjbz_165108/fgzc_165109/gjj_165110/'

def _get(url):
    x = urlparse(url)
    if x.scheme != 'https' or x.hostname != 'mzj.cq.gov.cn' or (not x.path.startswith('/zwgk_218/fdzdgknr/zdlyxxgk/lnrfl/ylfwzcjbz_165108/fgzc_165109/gjj_165110/')) or x.query or x.fragment:
        raise ValueError('仅允许重庆民政国家级养老政策栏目')
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
            elif 'Content' in dict(attrs).get('class', '').split():
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

def elder_policy_list(keyword=''):
    p = _Links()
    p.feed(_get(BASE + 'index.html'))
    out = []
    for href, title in p.links:
        url = urljoin(BASE, href)
        if re.fullmatch(re.escape(BASE) + '\\d{6}/t\\d{8}_\\d+\\.html', url) and keyword in title:
            out.append({'title': title, 'url': url})
    return out

def elder_policy_detail(url):
    p = _Body()
    p.feed(_get(url))
    text = '\n'.join((s.strip() for s in ''.join(p.parts).splitlines() if s.strip()))
    if len(text) < 100:
        raise ValueError('未识别正文')
    return {'url': url, 'text': text, 'note': '重庆市民政局国家级养老政策栏目本地转载页面；只覆盖本域链接，效力及附件请核对发布机关。'}
