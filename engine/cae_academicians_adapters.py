"""中国工程院公开院士名单与简介。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
BASE = 'https://www.cae.cn'
INDEX = BASE + '/cae/html/main/col48/column_48_1.html'

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
        h = a.get('href', '')
        if t == 'a' and re.fullmatch('/cae/html/main/colys/\\d+\\.html', h):
            self.path = h
            self.parts = []

    def handle_data(self, s):
        if self.path:
            self.parts.append(s)

    def handle_endtag(self, t):
        if t == 'a' and self.path:
            name = ' '.join(''.join(self.parts).split())
            if name:
                self.items[self.path] = {'name': name, 'path': self.path, 'url': BASE + self.path}
            self.path = None

class Body(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.parts = []

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'div':
            if self.depth:
                self.depth += 1
            elif 'intro' in a.get('class', '').split():
                self.depth = 1
        if self.depth and t in ('p', 'br'):
            self.parts.append('\n')

    def handle_data(self, s):
        if self.depth:
            self.parts.append(s)

    def handle_endtag(self, t):
        if t == 'div' and self.depth:
            self.depth -= 1

def cae_academicians(keyword=''):
    p = Catalog()
    p.feed(fetch(INDEX))
    if not p.items:
        raise ValueError('未识别工程院院士名单')
    return {'source': '中国工程院院士名单', 'source_url': INDEX, 'items': [i for i in p.items.values() if keyword in i['name']], 'note': '当前名单标题筛选；重名按路径和简介区分，不自动合并外籍或已故院士名单。'}

def cae_academician_detail(path):
    matches = [i for i in cae_academicians()['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在当前名单')
    p = Body()
    p.feed(fetch(matches[0]['url']))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if not text:
        raise ValueError('未识别简介')
    return {'source': '中国工程院院士名单', **matches[0], 'text': text, 'note': '官网简介可能不是实时履历，以官网为准。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(cae_academicians(a.keyword) if a.cmd == 'list' else cae_academician_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
