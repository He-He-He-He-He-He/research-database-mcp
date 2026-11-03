"""最高人民检察院工作报告公开目录，只读。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urljoin
BASE = 'https://www.spp.gov.cn'
INDEX = BASE + '/spp/gzbg/index.shtml'

def fetch(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True)
    if p.returncode:
        raise RuntimeError('上游请求失败（curl 状态 %d）' % p.returncode)
    return p.stdout.decode('utf-8')

class Catalog(HTMLParser):

    def __init__(self):
        super().__init__()
        self.item = None
        self.parts = []
        self.items = []

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        h = a.get('href', '')
        if t == 'a' and re.fullmatch('/spp/gzbg/\\d{6}/t\\d{8}_\\d+\\.shtml', h):
            self.item = h
            self.parts = []

    def handle_data(self, s):
        if self.item:
            self.parts.append(s)

    def handle_endtag(self, t):
        if t == 'a' and self.item:
            title = ' '.join(''.join(self.parts).split())
            if title:
                self.items.append({'path': self.item, 'title': title, 'url': BASE + self.item})
            self.item = None

class Body(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.parts = []
        self.images = []

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'div':
            if self.depth:
                self.depth += 1
            elif a.get('id') == 'fontzoom':
                self.depth = 1
        if self.depth and t in ('p', 'br', 'tr'):
            self.parts.append('\n')
        if self.depth and t in ('td', 'th'):
            self.parts.append('\t')
        if self.depth and t == 'img' and a.get('src'):
            self.images.append(a['src'])

    def handle_data(self, s):
        if self.depth:
            self.parts.append(s)

    def handle_endtag(self, t):
        if self.depth and t == 'div':
            self.depth -= 1

def spp_reports(keyword=''):
    p = Catalog()
    p.feed(fetch(INDEX))
    if not p.items:
        raise ValueError('未识别最高检工作报告目录')
    return {'source': '最高人民检察院工作报告', 'source_url': INDEX, 'items': [i for i in p.items if keyword in i['title']], 'note': '仅按工作报告目录标题筛选，并非检察全站、办案统计数据库或案例库。'}

def spp_report_detail(path):
    matches = [i for i in spp_reports()['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在当前工作报告目录')
    url = matches[0]['url']
    p = Body()
    p.feed(fetch(url))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if not text:
        raise ValueError('未识别正文')
    return {'source': '最高人民检察院工作报告', 'title': matches[0]['title'], 'url': url, 'text': text, 'note': '只提取文字，图片、表格关系与统计口径请核对原文。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(spp_reports(a.keyword) if a.cmd == 'list' else spp_report_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
