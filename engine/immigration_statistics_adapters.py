"""国家移民管理局统计数据栏目，只读。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
BASE = 'https://www.nia.gov.cn'
INDEX = BASE + '/n741440/n741567/index.html'

def fetch(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True)
    if p.returncode:
        raise RuntimeError('上游请求失败（curl 状态 %d）' % p.returncode)
    return p.stdout.decode('utf-8')

class Catalog(HTMLParser):

    def __init__(self):
        super().__init__()
        self.path = None
        self.parts = []
        self.items = {}

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        u = urljoin(INDEX, a.get('href', ''))
        x = urlsplit(u)
        if t == 'a' and x.scheme == 'https' and (x.hostname == 'www.nia.gov.cn') and re.fullmatch('/n741440/n741567/c\\d+/content\\.html', x.path):
            self.path = x.path
            self.parts = []

    def handle_data(self, s):
        if self.path:
            self.parts.append(s)

    def handle_endtag(self, t):
        if t == 'a' and self.path:
            title = ' '.join(''.join(self.parts).split())
            if title:
                self.items[self.path] = {'path': self.path, 'title': title, 'url': BASE + self.path}
            self.path = None

class Body(HTMLParser):

    def __init__(self):
        super().__init__()
        self.active = False
        self.parts = []
        self.title = ''

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'meta' and a.get('name') == 'ArticleTitle':
            self.title = a.get('content', '')
        if t == 'li' and a.get('id') == 'content':
            self.active = True
        if self.active and t in ('p', 'br', 'tr'):
            self.parts.append('\n')

    def handle_data(self, s):
        if self.active:
            self.parts.append(s)

    def handle_endtag(self, t):
        if self.active and t == 'li':
            self.active = False

def immigration_statistics(keyword=''):
    p = Catalog()
    p.feed(fetch(INDEX))
    if not p.items:
        raise ValueError('未识别移民管理统计目录')
    return {'source': '国家移民管理局统计数据', 'source_url': INDEX, 'items': [i for i in p.items.values() if keyword in i['title']], 'note': '仅筛选当前栏目首页标题，非个人出入境记录、全部历史或结构化数据库。'}

def immigration_statistic_detail(path):
    matches = [i for i in immigration_statistics()['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在当前栏目首页')
    url = matches[0]['url']
    p = Body()
    p.feed(fetch(url))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if not p.title or not text:
        raise ValueError('未识别统计正文')
    return {'source': '国家移民管理局统计数据', 'title': p.title, 'url': url, 'text': text, 'note': '文字提取；指标统计口径和单位请核对原文。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(immigration_statistics(a.keyword) if a.cmd == 'list' else immigration_statistic_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
