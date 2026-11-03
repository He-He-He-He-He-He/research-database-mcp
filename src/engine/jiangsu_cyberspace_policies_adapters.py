"""江苏网信网法规文件目录和公开正文。"""
import release_runtime
import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from nppa_statistics_adapters import fetch
from nppa_regulations_adapters import _Body
BASE = 'https://www.jswx.gov.cn/zhengce/fagui/'

class _Catalog(HTMLParser):

    def __init__(self):
        super().__init__()
        self.tit = False
        self.href = None
        self.parts = []
        self.items = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'div' and 'tit' in a.get('class', '').split():
            self.tit = True
        if self.tit and tag == 'a':
            self.href = a.get('href', '')
            self.parts = []

    def handle_data(self, text):
        if self.href:
            self.parts.append(text)

    def handle_endtag(self, tag):
        if tag == 'a' and self.href:
            url = urljoin(BASE, self.href)
            p = urlsplit(url)
            title = ' '.join(''.join(self.parts).split())
            if p.scheme == 'https' and p.hostname == 'www.jswx.gov.cn' and re.fullmatch('/(?:[\\w-]+/)+\\d{6}/t\\d{8}_\\d+\\.shtml', p.path) and title:
                self.items.append({'title': title, 'url': url})
            self.href = None
        if tag == 'div' and self.tit:
            self.tit = False

def jiangsu_cyberspace_policies(keyword=''):
    parser = _Catalog()
    parser.feed(fetch(BASE).decode('utf-8'))
    if not parser.items:
        raise ValueError('未识别目录，网站可能改版')
    return {'source_url': BASE, 'items': [x for x in parser.items if keyword.casefold() in x['title'].casefold()], 'scope': '只筛选当前栏目页面同站标题；包含政策、标准、解读及报道，不代表全量法规。'}

def jiangsu_cyberspace_policy_detail(url):
    p = urlsplit(url)
    if p.scheme != 'https' or p.hostname != 'www.jswx.gov.cn' or p.query or p.fragment or (not re.fullmatch('/(?:[\\w-]+/)+\\d{6}/t\\d{8}_\\d+\\.shtml', p.path)):
        raise ValueError('仅支持江苏网信网同站文章链接')
    parser = _Body('TRS_Editor')
    parser.feed(fetch(url).decode('utf-8'))
    text = '\n'.join((s.strip() for s in ''.join(parser.text).splitlines() if s.strip()))
    if not parser.found or len(text) < 100:
        raise ValueError('未识别正文')
    return {'source_url': url, 'text': text, 'note': '可能为政策转载、解读或新闻；颁布机关、施行时间与最新效力应查权威原件。'}
