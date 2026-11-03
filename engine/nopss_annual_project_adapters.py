"""全国哲学社会科学工作办公室国家社科基金年度项目公告。"""
import release_runtime
import re
import subprocess
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from szse_chinext_adapters import _Links
BASE = 'https://www.nopss.gov.cn'
INDEX = BASE + '/GB/219469/431027/'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.nopss.gov.cn' or (not (p.path.startswith('/GB/219469/431027/') or re.fullmatch('/n1/\\d{4}/\\d{4}/c431027-\\d+\\.html', p.path))) or p.query or p.fragment:
        raise ValueError('仅允许国家社科基金年度项目栏目')
    return release_runtime.run(['curl', '--compressed', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout.decode('utf-8')

class _Body(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.skip = 0
        self.parts = []
        self.links = []
        self.href = None
        self.at = []

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'div':
            if self.depth:
                self.depth += 1
            elif 'text_con' in a.get('class', '').split():
                self.depth = 1
        if self.depth and t in ('style', 'script'):
            self.skip += 1
        if self.depth and (not self.skip) and (t in ('p', 'br', 'h1', 'h2')):
            self.parts.append('\n')
        if self.depth and t == 'a':
            self.href = a.get('href')
            self.at = []

    def handle_data(self, s):
        if self.depth and (not self.skip):
            self.parts.append(s)
        if self.href is not None:
            self.at.append(s)

    def handle_endtag(self, t):
        if t == 'a' and self.href is not None:
            self.links.append({'title': ' '.join(''.join(self.at).split()), 'url': self.href})
            self.href = None
        if self.depth and t in ('style', 'script') and self.skip:
            self.skip -= 1
        if t == 'div' and self.depth:
            self.depth -= 1

def social_science_annual_list(page=1, keyword=''):
    if isinstance(page, bool) or not (isinstance(page, int) or (isinstance(page, str) and page.isascii() and page.isdigit())):
        raise ValueError('页码须为整数')
    if not isinstance(keyword, str):
        raise ValueError('关键词须为字符串')
    page = int(page)
    if not 1 <= page <= 100:
        raise ValueError('页码超出范围')
    p = _Links()
    p.feed(_get(INDEX if page == 1 else urljoin(INDEX, f'index{page - 1}.html')))
    out = []
    recognized = False
    for href, title in p.links:
        if re.fullmatch('/n1/\\d{4}/\\d{4}/c431027-\\d+\\.html', href) and title:
            recognized = True
            if keyword in title:
                out.append({'title': title, 'url': BASE + href})
    if not recognized:
        raise ValueError('未识别年度项目栏目，无法确认检索结果')
    return out

def social_science_annual_detail(url):
    p = _Body()
    p.feed(_get(url))
    text = '\n'.join((s.strip() for s in ''.join(p.parts).splitlines() if s.strip()))
    if len(text) < 30:
        raise ValueError('未识别公告正文')
    links = [{'title': x['title'], 'url': urljoin(url, x['url'])} for x in p.links if x['url'] and re.search('\\.(?:pdf|xlsx?|docx?)$', urlparse(x['url']).path, re.I)]
    return {'url': url, 'text': text, 'attachments': links, 'note': '年度项目公告正文及链接；附件可能由外部站点 HTTP 提供，不自动下载或解析。'}
