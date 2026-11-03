"""应急管理部自然灾害统计报告目录及正文，只读。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
ROOT = 'https://www.mem.gov.cn'
BASE = ROOT + '/gk/tjsj/'

def fetch_compressed(url):
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True)
    if r.returncode:
        raise RuntimeError('上游请求失败（curl 状态 %s）' % r.returncode)
    return r.stdout.decode('utf-8')

class List(HTMLParser):

    def __init__(self):
        super().__init__()
        self.url = None
        self.title = []
        self.date = []
        self.in_date = False
        self.items = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        u = a.get('href', '')
        if tag == 'a' and re.fullmatch('\\.\\./\\.\\./xw/yjglbgzdt/\\d{6}/t\\d{8}_\\d+\\.shtml', u):
            self.url = urljoin(BASE, u)
            self.title = []
            self.date = []
        if self.url and tag == 'span':
            self.in_date = True

    def handle_data(self, s):
        if self.url:
            (self.date if self.in_date else self.title).append(s)

    def handle_endtag(self, tag):
        if tag == 'span':
            self.in_date = False
        if tag == 'a' and self.url:
            t = ' '.join(''.join(self.title).split())
            if '自然灾害' in t:
                self.items.append({'title': t, 'date': ' '.join(''.join(self.date).split()), 'url': self.url})
            self.url = None

class Article(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.found = False
        self.text = []
        self.title = ''

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and a.get('name') == 'ArticleTitle':
            self.title = a.get('content', '')
        if not self.depth and tag == 'div' and ('TRS_Editor' in a.get('class', '').split()):
            self.depth = 1
            self.found = True
            return
        if self.depth and tag == 'div':
            self.depth += 1
        if self.depth and tag in ('p', 'br'):
            self.text.append('\n')

    def handle_data(self, s):
        if self.depth:
            self.text.append(s)

    def handle_endtag(self, tag):
        if self.depth and tag == 'div':
            self.depth -= 1

def emergency_list(keyword=''):
    p = List()
    p.feed(fetch_compressed(BASE))
    if not p.items:
        raise ValueError('未识别统计数据目录')
    return {'source': '应急管理部统计数据', 'source_url': BASE, 'scope': '当前目录页自然灾害报告，标题筛选', 'items': [x for x in p.items if keyword in x['title']], 'note': '历史灾情报告，非实时预警或完整灾害数据库。'}

def emergency_detail(url):
    x = urlsplit(url)
    if x.scheme != 'https' or x.netloc != 'www.mem.gov.cn' or x.query or x.fragment or (not re.fullmatch('/xw/yjglbgzdt/\\d{6}/t\\d{8}_\\d+\\.shtml', x.path)):
        raise ValueError('仅支持目录所列的应急管理部报告地址')
    p = Article()
    p.feed(fetch_compressed(url))
    if not p.found:
        raise ValueError('未识别正文')
    return {'source_url': url, 'title': p.title, 'text': ''.join(p.text).strip(), 'note': '灾情数据可能为初步统计，口径和修订以原文为准。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('url')
    a = p.parse_args()
    print(json.dumps(emergency_list(a.keyword) if a.cmd == 'list' else emergency_detail(a.url), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
