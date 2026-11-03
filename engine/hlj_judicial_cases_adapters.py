"""黑龙江省司法厅典型案例栏目，读取当前首页并按标题筛选。"""
import release_runtime
import argparse, json, re, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from research import fetch
BASE = 'https://sft.hlj.gov.cn'
LIST = BASE + '/sft/c115715/public_list.shtml'

class Listing(HTMLParser):

    def __init__(self):
        super().__init__()
        self.ul = False
        self.items = []
        self.date = False

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'ul' and a.get('id') == 'list':
            self.ul = True
        if self.ul and t == 'a':
            self.items.append({'title': a.get('title', '').strip(), 'url': urljoin(BASE, a.get('href', '')), 'list_date': ''})
        if self.ul and t == 'span' and ('date' in a.get('class', '').split()):
            self.date = True

    def handle_data(self, d):
        if self.date and self.items:
            self.items[-1]['list_date'] += d.strip()

    def handle_endtag(self, t):
        if t == 'span':
            self.date = False
        if t == 'ul' and self.ul:
            self.ul = False

class Article(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.seen = False
        self.parts = []
        self.meta = {}

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'meta' and a.get('name') in ('ArticleTitle', 'PubDate'):
            self.meta[a['name']] = a.get('content', '')
        if t == 'div' and a.get('id') == 'zoomcon':
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

def list_cases(keyword=''):
    p = Listing()
    p.feed(fetch(LIST))
    if not p.items:
        raise ValueError('未发现栏目列表，可能网站改版')
    return {'source': LIST, 'scope': '当前首页条目标题筛选，不覆盖全部历史', 'total_on_page': len(p.items), 'items': [x for x in p.items if keyword.casefold() in x['title'].casefold()]}

def detail(url):
    u = urlparse(url)
    if u.scheme != 'https' or u.netloc != 'sft.hlj.gov.cn' or (not re.fullmatch('/sft/c115715/\\d{6}/c00_\\d+\\.shtml', u.path)) or u.query or u.fragment:
        raise ValueError('只能读取本栏目内官方文章链接')
    p = Article()
    p.feed(fetch(url))
    if not p.seen:
        raise ValueError('未发现文章正文')
    return {'source': url, 'title': p.meta.get('ArticleTitle'), 'page_pubdate': p.meta.get('PubDate'), 'text': ''.join(p.parts).strip()}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('--keyword', default='')
    q = s.add_parser('detail')
    q.add_argument('url')
    a = p.parse_args()
    print(json.dumps(list_cases(a.keyword) if a.cmd == 'list' else detail(a.url), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
