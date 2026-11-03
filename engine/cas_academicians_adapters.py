"""中国科学院学部公开院士名单与简介。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urlsplit, urljoin
BASE = 'https://casad.cas.cn/ysxx2022/ysmd/'
DEPARTMENTS = {'sxwl': '数学物理学部', 'hxb': '化学部', 'smkx': '生命科学和医学学部', 'dxb': '地学部', 'xxjs': '信息技术科学部', 'jskx': '技术科学部'}

def fetch(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True)
    if p.returncode:
        raise RuntimeError('上游请求失败（curl 状态 %d）' % p.returncode)
    return p.stdout.decode('utf-8')

class Catalog(HTMLParser):

    def __init__(self, dept):
        super().__init__()
        self.dept = dept
        self.path = None
        self.parts = []
        self.items = {}

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        u = urljoin(BASE + self.dept + '/', a.get('href', ''))
        x = urlsplit(u)
        if t == 'a' and x.hostname == 'casad.cas.cn' and re.fullmatch('/ysxx2022/ysmd/' + self.dept + '/\\d{6}/t\\d{8}_\\d+\\.html', x.path):
            self.path = x.path
            self.parts = []

    def handle_data(self, s):
        if self.path:
            self.parts.append(s)

    def handle_endtag(self, t):
        if t == 'a' and self.path:
            name = ' '.join(''.join(self.parts).split())
            if name:
                self.items[self.path] = {'name': name, 'path': self.path, 'url': 'https://casad.cas.cn' + self.path}
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
            elif 'acadTxt' in a.get('class', '').split():
                self.depth = 1
        if self.depth and t in ('p', 'br'):
            self.parts.append('\n')

    def handle_data(self, s):
        if self.depth:
            self.parts.append(s)

    def handle_endtag(self, t):
        if self.depth and t == 'div':
            self.depth -= 1

def cas_academicians(keyword='', department='smkx'):
    if department not in DEPARTMENTS:
        raise ValueError('学部代码应为 ' + ','.join(DEPARTMENTS))
    p = Catalog(department)
    p.feed(fetch(BASE + department + '/'))
    if not p.items:
        raise ValueError('未识别院士名单')
    return {'source': '中国科学院学部院士名单', 'department': DEPARTMENTS[department], 'source_url': BASE + department + '/', 'items': [i for i in p.items.values() if keyword in i['name']], 'note': '仅当前指定学部在站名单，重名以链接和简介区分；其他学部、外籍院士及历史名录不自动合并。'}

def cas_academician_detail(department, path):
    matches = [i for i in cas_academicians('', department)['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在指定学部当前名单')
    p = Body()
    p.feed(fetch(matches[0]['url']))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if not text:
        raise ValueError('未识别院士简介')
    return {'source': '中国科学院学部院士名单', 'department': DEPARTMENTS[department], **matches[0], 'text': text, 'note': '官网简介可能不是实时履历，信息以发布页面为准。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q.add_argument('--department', choices=list(DEPARTMENTS), default='smkx')
    q = s.add_parser('detail')
    q.add_argument('department', choices=list(DEPARTMENTS))
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(cas_academicians(a.keyword, a.department) if a.cmd == 'list' else cas_academician_detail(a.department, a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
