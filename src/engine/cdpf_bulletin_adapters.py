"""中国残联残疾人事业发展统计公报目录及正文。"""
import release_runtime
import re
import subprocess
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from szse_chinext_adapters import _Links
BASE = 'https://www.cdpf.org.cn/zwgk/zccx/tjgb/'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.cdpf.org.cn' or (not p.path.startswith('/zwgk/zccx/tjgb/')) or p.query or p.fragment:
        raise ValueError('仅允许中国残联统计公报栏目')
    return release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout.decode('utf-8')

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
            elif dict(attrs).get('id') == 'article':
                self.depth = 1
        if self.depth and t in ('style', 'script'):
            self.skip += 1
        if self.depth and (not self.skip) and (t in ('p', 'br')):
            self.parts.append('\n')

    def handle_data(self, s):
        if self.depth and (not self.skip):
            self.parts.append(s)

    def handle_endtag(self, t):
        if self.depth and t in ('style', 'script') and self.skip:
            self.skip -= 1
        if t == 'div' and self.depth:
            self.depth -= 1

def disability_bulletins(keyword=''):
    p = _Links()
    p.feed(_get(BASE + 'index.htm'))
    items = []
    for href, title in p.links:
        url = urljoin(BASE, href)
        if re.fullmatch(re.escape(BASE) + '[a-f0-9]{32}\\.htm', url) and '残疾人事业发展统计公报' in title and (keyword in title):
            items.append({'title': title, 'url': url})
    if not items and (not keyword):
        raise ValueError('未找到统计公报目录')
    return items

def disability_bulletin_detail(url):
    p = _Body()
    p.feed(_get(url))
    content = '\n'.join((s.strip() for s in ''.join(p.parts).splitlines() if s.strip()))
    if len(content) < 100:
        raise ValueError('未识别公报正文')
    return {'url': url, 'text': content, 'note': '年度统计公报正文；图片不进行 OCR，指标定义和覆盖以原文为准。'}
