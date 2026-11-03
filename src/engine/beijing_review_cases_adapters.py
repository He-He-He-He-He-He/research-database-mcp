"""北京市司法局行政复议栏目页和公开正文。"""
import release_runtime
import argparse, json, re, sys
from html.parser import HTMLParser
from urllib.parse import urljoin
from research import fetch
BASE = 'https://sfj.beijing.gov.cn'
PATH = '/sfj/index/xzfyal/'

class Listing(HTMLParser):

    def __init__(self):
        super().__init__()
        self.items = []
        self.in_date = False

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'a' and re.fullmatch(PATH + '\\d+/index\\.html', a.get('href', '')):
            self.items.append({'title': a.get('title', ''), 'url': urljoin(BASE, a['href']), 'date': ''})
        if t == 'span' and self.items:
            self.in_date = True

    def handle_data(self, d):
        if self.in_date and self.items and re.fullmatch('\\d{4}-\\d{2}-\\d{2}', d.strip()):
            self.items[-1]['date'] = d.strip()

    def handle_endtag(self, t):
        if t == 'span':
            self.in_date = False

class Article(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.seen = False
        self.parts = []

    def handle_starttag(self, t, attrs):
        if t == 'div' and (not self.depth) and ('datail_con' in dict(attrs).get('class', '').split()):
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

def list_cases(page=1, keyword=''):
    if not 1 <= page <= 100:
        raise ValueError('页码须为 1 至 100')
    url = BASE + PATH + ('index.html' if page == 1 else 'sfj_f2ad-' + str(page) + '.html')
    p = Listing()
    p.feed(fetch(url))
    if not p.items:
        raise ValueError('该页未取得结果，可能超出页数或网站改版')
    return {'source': url, 'page': page, 'scope': '仅筛选当前页标题；栏目还包含政策、新闻', 'items': [x for x in p.items if keyword.casefold() in x['title'].casefold()]}

def detail(id):
    if not re.fullmatch('\\d{1,12}', str(id)):
        raise ValueError('页面 ID 须为数字')
    url = BASE + PATH + str(id) + '/index.html'
    p = Article()
    p.feed(fetch(url))
    if not p.seen:
        raise ValueError('未找到正文，页面可能改版')
    return {'source': url, 'text': ''.join(p.parts).strip()}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('--page', type=int, default=1)
    q.add_argument('--keyword', default='')
    q = s.add_parser('detail')
    q.add_argument('id')
    a = p.parse_args()
    print(json.dumps(list_cases(a.page, a.keyword) if a.cmd == 'list' else detail(a.id), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
