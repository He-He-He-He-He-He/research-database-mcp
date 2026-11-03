"""中国就业网公开内容检索及正文读取；适用于劳动争议研究。"""
import release_runtime
import argparse, json, re, sys
from html.parser import HTMLParser
from urllib.parse import urlencode, urlparse
from research import fetch
BASE = 'https://chinajob.mohrss.gov.cn'

class Results(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.items = []
        self.mode = ''
        self.total = None
        self.in_total = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cl = a.get('class', '').split()
        if tag == 'div' and 'result-total' in cl:
            self.in_total = True
        if self.in_total and tag == 'i' and ('normal' in cl):
            self.mode = 'total'
        if tag == 'div' and 'c-lists' in cl:
            self.depth = 1
            self.items.append({'title': '', 'url': '', 'snippet': ''})
            return
        if self.depth:
            if tag == 'div':
                self.depth += 1
            if tag == 'a' and (not self.items[-1]['url']):
                self.items[-1]['url'] = a.get('href', '')
                self.items[-1]['title'] = a.get('title', '')
                self.mode = 'title'
            elif tag == 'p':
                self.mode = 'snippet'

    def handle_data(self, t):
        if self.mode == 'total' and t.strip().isdigit():
            self.total = int(t.strip())
        if self.depth and self.mode == 'snippet':
            self.items[-1]['snippet'] += t
        if self.depth and self.mode == 'title' and (not self.items[-1]['title']):
            self.items[-1]['title'] += t

    def handle_endtag(self, tag):
        if tag in ('a', 'p', 'i'):
            self.mode = ''
        if tag == 'div' and self.depth:
            self.depth -= 1
        elif tag == 'div' and self.in_total:
            self.in_total = False

class Article(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.seen = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == 'div' and (not self.depth) and ('detail_article' in dict(attrs).get('class', '').split()):
            self.depth = 1
            self.seen = True
            return
        if self.depth:
            if tag == 'div':
                self.depth += 1
            if tag in ('br', 'p'):
                self.parts.append('\n')

    def handle_data(self, t):
        if self.depth:
            self.parts.append(t)

    def handle_endtag(self, tag):
        if tag == 'div' and self.depth:
            self.depth -= 1
        if tag == 'p' and self.depth:
            self.parts.append('\n')

def search(query, page=1):
    if not query.strip() or not 1 <= page <= 1000:
        raise ValueError('关键词不能为空，页码需在 1 至 1000')
    url = BASE + '/zcms/search/result?' + urlencode({'Query': query, 'SiteID': 1, 'TitleOnly': 'N', 'usingSynonym': 'N', 'PageIndex': page})
    p = Results()
    p.feed(fetch(url))
    if p.total is None:
        raise ValueError('搜索页面格式改变或请求被拒绝')
    return {'source': url, 'query': query, 'page': page, 'total': p.total, 'items': p.items, 'note': '站内检索覆盖就业、政策和案例等公开文章；结果并非完整的劳动仲裁或裁判文书数据库。'}

def detail(url):
    u = urlparse(url)
    if u.scheme != 'https' or u.netloc != 'chinajob.mohrss.gov.cn' or (not re.fullmatch('/c/\\d{4}-\\d{2}-\\d{2}/\\d+\\.shtml', u.path)) or u.query or u.fragment:
        raise ValueError('只支持本网站搜索结果中的文章地址')
    p = Article()
    p.feed(fetch(url))
    if not p.seen:
        raise ValueError('正文未找到；站点可能改版')
    return {'source': url, 'text': ''.join(p.parts).strip()}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('search')
    q.add_argument('query')
    q.add_argument('--page', type=int, default=1)
    q = s.add_parser('detail')
    q.add_argument('url')
    a = p.parse_args()
    print(json.dumps(search(a.query, a.page) if a.cmd == 'search' else detail(a.url), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
