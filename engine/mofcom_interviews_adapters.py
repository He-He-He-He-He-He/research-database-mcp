"""商务部在线访谈：跨年度目录与文字实录。"""
import release_runtime
import re, subprocess
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
BASE = 'https://interview.mofcom.gov.cn'
KINDS = {'领导访谈': '10001', '专题访谈': '10008'}

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'interview.mofcom.gov.cn' or (not (p.path == '/channel/interview/listByYear.shtml' or re.fullmatch('/detail/\\d{6}/[A-Za-z0-9]+\\.html', p.path))):
        raise ValueError('仅允许商务部访谈目录及详情地址')
    return release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '25', '--location', '--max-redirs', '0', url], check=True, capture_output=True).stdout.decode('utf-8-sig')

class _List(HTMLParser):

    def __init__(self):
        super().__init__()
        self.in_li = False
        self.anchor = None
        self.entries = []
        self.item = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = a.get('class', '').split()
        if tag == 'li' and 'col-lg-3' in classes:
            self.in_li = True
            self.item = []
        if self.in_li and tag == 'a' and ('aTitle1' in classes):
            self.anchor = {'url': urljoin(BASE, a.get('href', '')), 'text': []}

    def handle_data(self, text):
        if self.anchor is not None:
            self.anchor['text'].append(text)

    def handle_endtag(self, tag):
        if tag == 'a' and self.anchor is not None:
            self.anchor['text'] = ' '.join(''.join(self.anchor['text']).split())
            self.item.append(self.anchor)
            self.anchor = None
        if tag == 'li' and self.in_li:
            if self.item:
                r = {'url': self.item[0]['url']}
                for item in self.item:
                    text = item['text']
                    for key in ('主题', '时间', '嘉宾'):
                        if text.startswith(key + '：'):
                            r[key] = text[len(key) + 1:].strip()
                if '主题' in r:
                    self.entries.append(r)
            self.in_li = False
            self.item = []

class _Transcript(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.found = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if self.depth and tag not in ('br', 'img', 'hr', 'input', 'meta', 'link'):
            self.depth += 1
        elif not self.depth and tag == 'div' and ('ft-word-box' in dict(attrs).get('class', '').split()):
            self.depth = 1
            self.found = True
        if self.depth and tag in ('p', 'br'):
            self.parts.append('\n')

    def handle_startendtag(self, tag, attrs):
        if self.depth and tag == 'br':
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if self.depth:
            self.depth -= 1

    def handle_data(self, text):
        if self.depth:
            self.parts.append(text)

def mofcom_interview_list(kind='领导访谈', year=None, keyword=''):
    if kind not in KINDS:
        raise ValueError('kind 仅支持 领导访谈、专题访谈')
    p = _List()
    p.feed(_get(f'{BASE}/channel/interview/listByYear.shtml?id={KINDS[kind]}'))
    if not p.entries:
        raise ValueError('目录未解析到记录，页面结构可能已变')
    needle = ''.join(keyword.split()).casefold()
    y = str(year) if year is not None else None
    return [r for r in p.entries if (y is None or r.get('时间', '').startswith(y)) and needle in ''.join((''.join(str(v).split()) for v in r.values())).casefold()]

def mofcom_interview_detail(url):
    p = _Transcript()
    p.feed(_get(url))
    text = '\n'.join((line.strip() for line in ''.join(p.parts).splitlines() if line.strip()))
    if not p.found:
        raise ValueError('未找到文字实录区域，页面结构可能变化')
    return {'url': url, 'text': text, 'note': '页面所载文字实录；若为空表示页面未提供可解析正文。'}
