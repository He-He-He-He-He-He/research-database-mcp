"""生态环境部应对气候变化履约信息目录，只读。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
BASE = 'https://www.mee.gov.cn/ywgz/ydqhbh/qhbhlf/'

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
        if t == 'a' and re.fullmatch('\\./\\d{6}/t\\d{8}_\\d+\\.shtml', h):
            self.item = h[2:]
            self.parts = []

    def handle_data(self, s):
        if self.item:
            self.parts.append(s)

    def handle_endtag(self, t):
        if t == 'a' and self.item:
            title = ' '.join(''.join(self.parts).split())
            if title:
                self.items.append({'path': self.item, 'title': title, 'url': urljoin(BASE, self.item)})
            self.item = None

class Body(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.parts = []
        self.links = []
        self.title = ''

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'meta' and a.get('name') == 'ArticleTitle':
            self.title = a.get('content', '')
        if t == 'div':
            if self.depth:
                self.depth += 1
            elif 'TRS_Editor' in a.get('class', '').split():
                self.depth = 1
        if self.depth and t in ('p', 'br', 'div', 'tr'):
            self.parts.append('\n')
        if self.depth and t == 'a' and a.get('href'):
            self.links.append(a['href'])

    def handle_data(self, s):
        if self.depth:
            self.parts.append(s)

    def handle_endtag(self, t):
        if t == 'div' and self.depth:
            self.depth -= 1

def climate_policy_list(keyword=''):
    p = Catalog()
    p.feed(fetch(BASE))
    if not p.items:
        raise ValueError('未识别履约栏目')
    return {'source': '生态环境部应对气候变化履约信息', 'source_url': BASE, 'items': [i for i in p.items if keyword in i['title']], 'note': '仅当前栏目首页按标题筛选，不是气候数据库或全站检索。'}

def climate_policy_detail(path):
    matches = [i for i in climate_policy_list()['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在当前目录')
    url = matches[0]['url']
    p = Body()
    p.feed(fetch(url))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if not text or not p.title:
        raise ValueError('未识别详情正文')
    attachments = []
    for link in p.links:
        u = urljoin(url, link)
        x = urlsplit(u)
        if x.scheme == 'https' and x.hostname == 'www.mee.gov.cn' and x.path.lower().endswith('.pdf'):
            attachments.append(u)
    return {'source': '生态环境部应对气候变化履约信息', 'title': p.title, 'url': url, 'text': text, 'pdf_links': attachments, 'note': '正文仅文字，PDF 链接未下载或解析；详情和报告请核对原文。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(climate_policy_list(a.keyword) if a.cmd == 'list' else climate_policy_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
