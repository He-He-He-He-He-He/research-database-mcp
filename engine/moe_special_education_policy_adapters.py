"""教育部特殊教育发展政策公开栏目。"""
import release_runtime
import re
import subprocess
from html.parser import HTMLParser
from urllib.parse import urlparse
from szse_chinext_adapters import _Links
INDEX = 'https://www.moe.gov.cn/jyb_xxgk/xxgk/neirong/fenlei/sxml_jcjy/jcjy_tsjy/tsjy_fzzc/'
API = 'https://www.moe.gov.cn/was5/web/search?channelid=251673&chnlid=2147442743&page='

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.moe.gov.cn' or (not (p.path == '/was5/web/search' or p.path.startswith('/srcsite/'))):
        raise ValueError('仅允许教育部栏目及政策页面')
    return release_runtime.run(['curl', '--location', '--max-redirs', '3', '--proto-redir', '=http,https', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout.decode('utf-8')

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
            elif dict(attrs).get('id') == 'downloadContent':
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

def special_education_list(page=1):
    page = int(page)
    if not 1 <= page <= 100:
        raise ValueError('页码超出范围')
    p = _Links()
    p.feed(_get(API + str(page)))
    out = []
    for href, title in p.links:
        x = urlparse(href)
        if x.hostname == 'www.moe.gov.cn' and re.fullmatch('/srcsite/[^/]+/[^/]+/\\d{6}/t\\d{8}_\\d+\\.html', x.path) and title:
            out.append({'title': title, 'url': 'https://www.moe.gov.cn' + x.path})
    if not out:
        raise ValueError('该页未找到政策条目')
    return out

def special_education_detail(url):
    p = _Body()
    p.feed(_get(url))
    text = '\n'.join((s.strip() for s in ''.join(p.parts).splitlines() if s.strip()))
    if len(text) < 100:
        raise ValueError('未识别政策正文')
    return {'url': url, 'text': text, 'note': '仅教育部特殊教育政策目录，附件和后续效力应核对官方页面。'}
