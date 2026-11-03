"""国家发展改革委规章公开目录及正文。"""
import release_runtime
import re
import subprocess
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from szse_chinext_adapters import _Links
BASE = 'https://zfxxgk.ndrc.gov.cn/web/'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'zfxxgk.ndrc.gov.cn' or p.path not in ('/web/zclist.jsp', '/web/iteminfo.jsp'):
        raise ValueError('仅允许发改委规章目录和详情')
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
            elif 'zhengwen' in dict(attrs).get('class', '').split():
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

def ndrc_rules(keyword=''):
    p = _Links()
    p.feed(_get(BASE + 'zclist.jsp?dirid=40'))
    out = []
    for href, title in p.links:
        if re.fullmatch('iteminfo\\.jsp\\?id=\\d+', href) and keyword in title:
            out.append({'title': title, 'id': href.split('=')[1], 'url': urljoin(BASE, href)})
    if not out and (not keyword):
        raise ValueError('未找到规章条目')
    return out

def ndrc_rule_detail(id):
    id = str(id)
    if not re.fullmatch('\\d{1,10}', id):
        raise ValueError('规章 ID 应为数字')
    url = BASE + 'iteminfo.jsp?id=' + id
    p = _Body()
    p.feed(_get(url))
    text = '\n'.join((s.strip() for s in ''.join(p.parts).splitlines() if s.strip()))
    if len(text) < 100:
        raise ValueError('未识别规章正文')
    return {'id': id, 'url': url, 'text': text, 'note': '发改委规章原文；施行日期、修改废止情况与最新效力须核对原页和后续公告。'}
