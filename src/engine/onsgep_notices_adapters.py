"""全国教育科学规划领导小组办公室通知公告。"""
import release_runtime
import re
import subprocess
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from szse_chinext_adapters import _Links
BASE = 'https://onsgep.moe.edu.cn'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'onsgep.moe.edu.cn' or (not (p.path == '/tzgg' or re.fullmatch('/post/view/\\d+', p.path))) or p.fragment or (p.query and (not re.fullmatch('page=\\d+', p.query))):
        raise ValueError('仅允许全国教育科学规划通知栏目')
    return release_runtime.run(['curl', '--compressed', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout.decode('utf-8')

class _Body(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.skip = 0
        self.parts = []
        self.href = None
        self.a = []
        self.links = []

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'div':
            if self.depth:
                self.depth += 1
            elif 'mce-content-body' in a.get('class', '').split():
                self.depth = 1
        if self.depth and t in ('style', 'script'):
            self.skip += 1
        if self.depth and (not self.skip) and (t in ('p', 'br', 'h1', 'h2')):
            self.parts.append('\n')
        if self.depth and t == 'a':
            self.href = a.get('href')
            self.a = []

    def handle_data(self, s):
        if self.depth and (not self.skip):
            self.parts.append(s)
        if self.href is not None:
            self.a.append(s)

    def handle_endtag(self, t):
        if t == 'a' and self.href is not None:
            self.links.append({'title': ' '.join(''.join(self.a).split()), 'url': self.href})
            self.href = None
        if self.depth and t in ('style', 'script') and self.skip:
            self.skip -= 1
        if t == 'div' and self.depth:
            self.depth -= 1

def education_planning_notices(keyword=''):
    p = _Links()
    p.feed(_get(BASE + '/tzgg'))
    out = []
    seen = set()
    for href, title in p.links:
        if re.fullmatch('/post/view/\\d+', href) and title and (keyword in title) and (href not in seen):
            seen.add(href)
            out.append({'title': ' '.join(title.split()), 'url': BASE + href})
    if not out and (not keyword):
        raise ValueError('未识别通知目录')
    return out

def education_planning_notice_detail(url):
    p = _Body()
    p.feed(_get(url))
    text = '\n'.join((s.strip() for s in ''.join(p.parts).splitlines() if s.strip()))
    attachments = []
    for x in p.links:
        if x['url'] and re.search('\\.(?:pdf|docx?|xlsx?)$', urlparse(x['url']).path, re.I):
            attachments.append({'title': x['title'], 'url': urljoin(url, x['url'])})
    if len(text) < 100:
        raise ValueError('未识别正文')
    return {'url': url, 'text': text, 'attachments': attachments, 'note': '全国教育科学规划通知公告正文和附件链接；具体申报要求、时效以最新发布为准。'}
