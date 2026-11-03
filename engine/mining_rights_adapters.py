"""自然资源部采矿权出让结果公示，只读。"""
import release_runtime
import argparse, json, re, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from research import fetch
BASE = 'https://ky.mnr.gov.cn/jggs/ckjjgs/'

class Listing(HTMLParser):

    def __init__(self):
        super().__init__()
        self.date = ''
        self.dateon = False
        self.url = None
        self.title = []
        self.items = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        u = a.get('href', '')
        if tag == 'span':
            self.dateon = True
            self.date = ''
        if tag == 'a' and re.fullmatch('\\./\\d{6}/t\\d{8}_\\d+\\.htm', u):
            self.url = urljoin(BASE, u)
            self.title = []

    def handle_data(self, s):
        if self.dateon:
            self.date += s
        if self.url:
            self.title.append(s)

    def handle_endtag(self, tag):
        if tag == 'span':
            self.dateon = False
        if tag == 'a' and self.url:
            self.items.append({'title': ' '.join(''.join(self.title).split()), 'date': self.date.strip(), 'url': self.url})
            self.url = None

class Article(HTMLParser):

    def __init__(self):
        super().__init__()
        self.inside = False
        self.found = False
        self.text = []
        self.title_on = False
        self.title = ''

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'title':
            self.title_on = True
        if tag == 'td' and a.get('id') == 'content1':
            self.inside = True
            self.found = True
        if self.inside and tag in ('p', 'br'):
            self.text.append('\n')

    def handle_data(self, s):
        if self.title_on:
            self.title += s
        if self.inside:
            self.text.append(s)

    def handle_endtag(self, tag):
        if tag == 'title':
            self.title_on = False
        if tag == 'td' and self.inside:
            self.inside = False

def mining_list(page=1, keyword=''):
    if not 1 <= page <= 100:
        raise ValueError('页码须为 1–100')
    u = BASE if page == 1 else BASE + 'index_' + str(page - 1) + '.htm'
    p = Listing()
    p.feed(fetch(u))
    if not p.items:
        raise ValueError('未识别采矿权公示目录')
    return {'source': '自然资源部门户采矿权出让结果公示', 'source_url': u, 'page': page, 'items': [x for x in p.items if keyword in x['title']], 'note': '关键词仅匹配当前页展示标题，标题可能被网站截断；不是全部矿业权数据。'}

def mining_detail(url):
    x = urlsplit(url)
    if x.scheme != 'https' or x.netloc != 'ky.mnr.gov.cn' or x.query or x.fragment or (not re.fullmatch('/jggs/ckjjgs/\\d{6}/t\\d{8}_\\d+\\.htm', x.path)):
        raise ValueError('只接受本目录内的采矿权公示地址')
    p = Article()
    p.feed(fetch(url))
    if not p.found:
        raise ValueError('未识别公示正文')
    return {'source_url': url, 'title': p.title.strip(), 'text': ''.join(p.text).strip(), 'note': '公示内容、时效、成交条件以原文为准。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('--page', type=int, default=1)
    q.add_argument('--keyword', default='')
    q = s.add_parser('detail')
    q.add_argument('url')
    a = p.parse_args()
    print(json.dumps(mining_list(a.page, a.keyword) if a.cmd == 'list' else mining_detail(a.url), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
