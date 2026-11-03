"""国家艺术基金年度资助项目名单公告及原表。"""
import release_runtime
import re, subprocess
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
BASE = 'https://www.cnaf.cn'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.cnaf.cn' or p.query or p.fragment or (not (p.path == '/project_list.html' or re.fullmatch('/project_list/p/\\d+\\.html', p.path) or re.fullmatch('/project_detail/\\d+\\.html', p.path))):
        raise ValueError('仅支持国家艺术基金名单栏目地址')
    return release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '30', '--max-redirs', '0', url], check=True, capture_output=True).stdout.decode('utf-8-sig')

class _List(HTMLParser):

    def __init__(self):
        super().__init__()
        self.active = False
        self.inlink = False
        self.row = None
        self.rows = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'div' and a.get('id') == 'ajax-list':
            self.active = True
        if self.active and tag == 'a' and re.fullmatch('/project_detail/\\d+\\.html', a.get('href', '')):
            self.inlink = True
            self.row = {'url': urljoin(BASE, a['href']), 'title': ''}

    def handle_data(self, text):
        if self.inlink:
            self.row['title'] += text

    def handle_endtag(self, tag):
        if tag == 'a' and self.inlink:
            self.row['title'] = self.row['title'].strip()
            self.rows.append(self.row)
            self.row = None
            self.inlink = False

class _Body(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.found = False
        self.parts = []
        self.images = []
        self.links = []
        self.table = None
        self.row = None
        self.cell = None
        self.tables = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if self.depth and tag not in ('br', 'img', 'hr', 'input', 'meta', 'link'):
            self.depth += 1
        elif not self.depth and tag == 'div' and ('article-cont' in a.get('class', '').split()):
            self.depth = 1
            self.found = True
        if not self.depth:
            return
        if tag in ('p', 'div', 'br', 'tr'):
            self.parts.append('\n')
        if tag == 'img' and a.get('src'):
            self.images.append(urljoin(BASE, a['src']))
        if tag == 'a' and a.get('href'):
            self.links.append(urljoin(BASE, a['href']))
        if tag == 'table' and self.table is None:
            self.table = []
        elif tag == 'tr' and self.table is not None:
            self.row = []
        elif tag in ('td', 'th') and self.row is not None:
            self.cell = []

    def handle_startendtag(self, tag, attrs):
        if self.depth and tag == 'img':
            src = dict(attrs).get('src')
            if src:
                self.images.append(urljoin(BASE, src))
        elif self.depth and tag == 'br':
            self.parts.append('\n')

    def handle_data(self, text):
        if self.depth:
            self.parts.append(text)
        if self.cell is not None:
            self.cell.append(text)

    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.cell is not None:
            self.row.append(' '.join(''.join(self.cell).split()))
            self.cell = None
        elif tag == 'tr' and self.row is not None:
            self.table.append(self.row)
            self.row = None
        elif tag == 'table' and self.table is not None:
            self.tables.append(self.table)
            self.table = None
        if self.depth and tag not in ('br', 'img', 'hr', 'input', 'meta', 'link'):
            self.depth -= 1

def cnaf_project_notices(page=1, keyword=''):
    page = int(page)
    if not 1 <= page <= 100:
        raise ValueError('页码必须在 1—100')
    url = BASE + ('/project_list.html' if page == 1 else f'/project_list/p/{page}.html')
    p = _List()
    p.feed(_get(url))
    if not p.rows:
        raise ValueError('名单目录为空或结构改变')
    needle = ''.join(keyword.split()).casefold()
    return [r for r in p.rows if needle in ''.join(r['title'].split()).casefold()]

def cnaf_project_notice_detail(url):
    p = _Body()
    p.feed(_get(url))
    if not p.found:
        raise ValueError('未识别名单公告正文')
    return {'url': url, 'text': '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip())), 'image_urls': p.images, 'links': p.links, 'tables': p.tables, 'note': '保留公告原文、图片和原表；公示不等于公示后最终变更状态。'}
