"""司法部智慧普法平台普法动态页面与正文，按当前页标题过滤。"""
import release_runtime
import argparse, json, re, sys
from html.parser import HTMLParser
from urllib.parse import urlparse, urlunparse
from research import fetch
BASE = 'https://legalinfo.moj.gov.cn'
PATH = '/zhfxfzzx/fzzxyw/'

class Listing(HTMLParser):

    def __init__(self):
        super().__init__()
        self.in_ul = False
        self.items = []
        self.in_a = False
        self.in_date = False

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'ul' and 'rightSide_list' in a.get('class', '').split():
            self.in_ul = True
        elif self.in_ul and t == 'a':
            u = urlparse(a.get('href', ''))
            if u.hostname == 'legalinfo.moj.gov.cn' and u.path.endswith('.html'):
                original = urlunparse(u)
                u = u._replace(scheme='https')
                self.items.append({'title': '', 'url': urlunparse(u), 'original_url': original, 'detail_supported': bool(re.fullmatch('/(?:pub/sfbzhfx/)?zhfxfzzx/fzzxyw/\\d{6}/t\\d{8}_\\d+\\.html', u.path)) and (not u.query) and (not u.fragment), 'date': ''})
                self.in_a = True
            elif u.scheme == 'https' and u.hostname == 'www.moj.gov.cn':
                self.items.append({'title': '', 'url': urlunparse(u), 'original_url': urlunparse(u), 'detail_supported': False, 'date': ''})
                self.in_a = True
        elif self.in_ul and t == 'span':
            self.in_date = True

    def handle_data(self, d):
        if self.items and self.in_a:
            self.items[-1]['title'] += d.strip()
        if self.items and self.in_date:
            match = re.search('\\d{4}-\\d{2}-\\d{2}', d)
            if match:
                self.items[-1]['date'] = match.group()

    def handle_endtag(self, t):
        if t == 'a':
            self.in_a = False
        if t == 'span':
            self.in_date = False
        if t == 'ul' and self.in_ul:
            self.in_ul = False

class Article(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.seen = False
        self.parts = []

    def handle_starttag(self, t, attrs):
        if t == 'div' and (not self.depth) and ('TRS_Editor' in dict(attrs).get('class', '').split()):
            self.depth = 1
            self.seen = True
            return
        if self.depth:
            if t == 'div':
                self.depth += 1
            if t in ('p', 'br'):
                self.parts.append('\n')

    def handle_data(self, d):
        if self.depth:
            self.parts.append(d)

    def handle_endtag(self, t):
        if t == 'div' and self.depth:
            self.depth -= 1
        if t == 'p' and self.depth:
            self.parts.append('\n')

def list_articles(page=1, keyword=''):
    if not 1 <= page <= 100:
        raise ValueError('页码须为 1 至 100')
    url = BASE + PATH + ('index.html' if page == 1 else 'index_' + str(page - 1) + '.html')
    p = Listing()
    p.feed(fetch(url))
    if not p.items:
        raise ValueError('未找到列表，页码可能超出或网站改版')
    return {'source': url, 'page': page, 'scope': '当前页标题筛选，包含转载、新闻与普法文章；司法部官方网站外链保留原网址但本工具详情接口不读取外链。', 'items': [x for x in p.items if keyword.casefold() in x['title'].casefold()]}

def detail(url):
    u = urlparse(url)
    if u.scheme != 'https' or u.netloc != 'legalinfo.moj.gov.cn' or (not re.fullmatch('/(?:pub/sfbzhfx/)?zhfxfzzx/fzzxyw/\\d{6}/t\\d{8}_\\d+\\.html', u.path)) or u.query or u.fragment:
        raise ValueError('仅接受本栏目文章链接')
    p = Article()
    p.feed(fetch(url))
    if not p.seen:
        raise ValueError('未找到正文，网站可能改版')
    return {'source': url, 'text': ''.join(p.parts).strip()}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('--page', type=int, default=1)
    q.add_argument('--keyword', default='')
    q = s.add_parser('detail')
    q.add_argument('url')
    a = p.parse_args()
    print(json.dumps(list_articles(a.page, a.keyword) if a.cmd == 'list' else detail(a.url), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
