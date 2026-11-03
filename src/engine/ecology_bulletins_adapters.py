"""生态环境部生态环境状况公报目录和 PDF 地址。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urljoin
BASE = 'https://www.mee.gov.cn/hjzl/sthjzk/'

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
        if t == 'a' and re.fullmatch('\\./[a-z0-9]+/\\d{6}/P\\d+\\.pdf', h, re.I):
            self.path = h[2:]
            self.parts = []

    def handle_data(self, s):
        if self.path:
            self.parts.append(s)

    def handle_endtag(self, t):
        if t == 'a' and self.path:
            title = ' '.join(''.join(self.parts).split())
            if title:
                self.items[self.path] = {'path': self.path, 'title': title, 'url': urljoin(BASE, self.path)}
            self.path = None

def ecology_bulletins(keyword=''):
    p = Catalog()
    p.feed(fetch(BASE))
    if not p.items:
        raise ValueError('未识别生态环境公报目录')
    return {'source': '生态环境部生态环境状况公报', 'source_url': BASE, 'items': [i for i in p.items.values() if keyword in i['title']], 'note': '当前目录中的 PDF 标题筛选；非结构化观测数据库。'}

def ecology_bulletin_detail(path):
    matches = [i for i in ecology_bulletins()['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在当前目录')
    return {'source': '生态环境部生态环境状况公报', **matches[0], 'format': 'PDF', 'note': '返回官方 PDF 链接，不下载或 OCR；可能是大体积扫描文件，数据需查看原文。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(ecology_bulletins(a.keyword) if a.cmd == 'list' else ecology_bulletin_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
