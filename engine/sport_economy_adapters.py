"""国家体育总局体育经济司公开信息栏目，只读。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
INDEX = 'https://www.sport.gov.cn/jjs/n5039/index.html'
BASE = 'https://www.sport.gov.cn'

def fetch(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True)
    if p.returncode:
        raise RuntimeError('上游请求失败（curl 状态 %d）' % p.returncode)
    return p.stdout.decode('utf-8')

class Catalog(HTMLParser):

    def __init__(self):
        super().__init__()
        self.items = {}

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        u = urljoin(INDEX, a.get('href', ''))
        x = urlsplit(u)
        title = a.get('title', '').strip()
        if t == 'a' and title and (x.hostname == 'www.sport.gov.cn') and re.fullmatch('/jjs/n5039/c\\d+/content\\.html', x.path):
            self.items[x.path] = {'path': x.path, 'title': title, 'url': BASE + x.path}

class Body(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.parts = []
        self.title = ''

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'meta' and a.get('name') == 'ArticleTitle':
            self.title = a.get('content', '')
        if t == 'table':
            if self.depth:
                self.depth += 1
            elif a.get('id') == 'zoom':
                self.depth = 1
        if self.depth and t in ('p', 'br', 'tr'):
            self.parts.append('\n')
        if self.depth and t in ('td', 'th'):
            self.parts.append('\t')

    def handle_data(self, s):
        if self.depth:
            self.parts.append(s)

    def handle_endtag(self, t):
        if t == 'table' and self.depth:
            self.depth -= 1

def sport_economy_list(keyword=''):
    p = Catalog()
    p.feed(fetch(INDEX))
    if not p.items:
        raise ValueError('未识别体育经济目录')
    return {'source': '国家体育总局体育经济司', 'source_url': INDEX, 'items': [i for i in p.items.values() if keyword in i['title']], 'note': '当前栏目首页标题筛选，非全站或完整体育统计数据库。'}

def sport_economy_detail(path):
    matches = [i for i in sport_economy_list()['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在当前目录首页')
    p = Body()
    p.feed(fetch(matches[0]['url']))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if not p.title or not text:
        raise ValueError('未识别正文')
    return {'source': '国家体育总局体育经济司', 'title': p.title, 'url': matches[0]['url'], 'text': text, 'note': '仅文字提取，表格结构与统计口径请核对原文。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(sport_economy_list(a.keyword) if a.cmd == 'list' else sport_economy_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
