"""国家移民管理局政策文件当前首页及站内正文。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
BASE = 'https://www.nia.gov.cn'
LIST = BASE + '/n741440/n741547/'

def fetch(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--location', '--compressed', '--max-time', '25', url], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.stdout.decode('utf-8')

class Listing(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.items = []
        self.a = False
        self.sp = False

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'div' and 'list_bd' in a.get('class', '').split():
            self.depth = 1
            return
        if self.depth and t == 'div':
            self.depth += 1
        if self.depth and t == 'a':
            self.items.append({'title': '', 'url': urljoin(LIST, a.get('href', '')), 'date': ''})
            self.a = True
        if self.depth and t == 'span':
            self.sp = True

    def handle_data(self, d):
        if self.items and self.depth and self.a:
            self.items[-1]['title'] += d.strip()
        if self.items and self.depth and self.sp:
            m = re.search('\\d{4}-\\d{2}-\\d{2}', d)
            if m:
                self.items[-1]['date'] = m.group()

    def handle_endtag(self, t):
        if t == 'a':
            self.a = False
        if t == 'span':
            self.sp = False
        if t == 'div' and self.depth:
            self.depth -= 1

class Article(HTMLParser):

    def __init__(self):
        super().__init__()
        self.active = False
        self.seen = False
        self.parts = []

    def handle_starttag(self, t, attrs):
        if t == 'li' and dict(attrs).get('id') == 'content':
            self.active = True
            self.seen = True
            return
        if self.active and t in ('p', 'br'):
            self.parts.append('\n')

    def handle_data(self, d):
        if self.active:
            self.parts.append(d)

    def handle_endtag(self, t):
        if self.active and t == 'li':
            self.active = False
        elif self.active and t == 'p':
            self.parts.append('\n')

def list_policies(keyword=''):
    p = Listing()
    p.feed(fetch(LIST))
    if not p.items:
        raise ValueError('未发现目录，上游可能改版')
    return {'source': LIST, 'scope': '当前首页标题筛选；存在跳转其他政府站点的条目', 'total_on_page': len(p.items), 'items': [x for x in p.items if keyword.casefold() in x['title'].casefold()]}

def detail(url):
    u = urlparse(url)
    if u.scheme != 'https' or u.netloc != 'www.nia.gov.cn' or (not re.fullmatch('/n741440/n741547/c\\d+/content\\.html', u.path)) or u.query or u.fragment:
        raise ValueError('正文仅支持目录中移民局本站链接')
    p = Article()
    p.feed(fetch(url))
    if not p.seen:
        raise ValueError('未找到正文，网站可能改版')
    return {'source': url, 'text': ''.join(p.parts).strip(), 'scope': '当前文章页面；不自动获取正文其他分页'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('--keyword', default='')
    q = s.add_parser('detail')
    q.add_argument('url')
    a = p.parse_args()
    print(json.dumps(list_policies(a.keyword) if a.cmd == 'list' else detail(a.url), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
