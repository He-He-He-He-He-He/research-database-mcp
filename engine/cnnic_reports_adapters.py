"""中国互联网络信息中心统计报告公开栏目。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
BASE = 'https://www.cnnic.cn'
INDEX = BASE + '/6/86/88/index.html'

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
        if t == 'a' and re.fullmatch('/n4/\\d{4}/\\d{4}/c88-\\d+\\.html', h):
            self.path = h
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
        self.depth = 0
        self.parts = []
        self.links = []

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'div':
            if self.depth:
                self.depth += 1
            elif 'inner-text' in a.get('class', '').split():
                self.depth = 1
        if self.depth and t in ('p', 'br', 'tr'):
            self.parts.append('\n')
        if self.depth and t == 'a' and a.get('href'):
            self.links.append(a['href'])

    def handle_data(self, s):
        if self.depth:
            self.parts.append(s)

    def handle_endtag(self, t):
        if t == 'div' and self.depth:
            self.depth -= 1

def cnnic_reports(keyword=''):
    p = Catalog()
    p.feed(fetch(INDEX))
    if not p.items:
        raise ValueError('未识别统计报告目录')
    return {'source': '中国互联网络信息中心统计报告', 'source_url': INDEX, 'items': [i for i in p.items.values() if keyword in i['title']], 'note': '仅当前目录首页标题；报告为抽样统计与分析，非实时用户明细。'}

def cnnic_report_detail(path):
    matches = [i for i in cnnic_reports()['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在当前目录首页')
    url = matches[0]['url']
    p = Body()
    p.feed(fetch(url))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    links = []
    for h in p.links:
        u = urljoin(url, h)
        x = urlsplit(u)
        if x.scheme == 'https' and x.hostname == 'www.cnnic.cn' and x.path.lower().endswith('.pdf'):
            links.append(u)
    if not text:
        raise ValueError('未识别报告发布文字')
    return {'source': '中国互联网络信息中心统计报告', **matches[0], 'text': text, 'pdf_links': links, 'note': '网页文字为报告介绍，完整报告以 PDF 为准；不解析附件或自动核验统计口径。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(cnnic_reports(a.keyword) if a.cmd == 'list' else cnnic_report_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
