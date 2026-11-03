"""北京市市场监管局食品监督公示。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, quote
BASE = 'https://scjgj.beijing.gov.cn/zwxx/gs/spzlgs/'

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
        h = a.get('href', '')
        title = a.get('title', '').strip()
        if t == 'a' and title and re.fullmatch('\\./\\d{6}/t\\d{8}_\\d+\\.html', h):
            self.items[h[2:]] = {'path': h[2:], 'title': title, 'url': urljoin(BASE, h)}

class Body(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.parts = []
        self.title = ''
        self.links = []

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'meta' and a.get('name') == 'ArticleTitle':
            self.title = a.get('content', '')
        if t == 'div':
            if self.depth:
                self.depth += 1
            elif 'TRS_UEDITOR' in a.get('class', '').split():
                self.depth = 1
        if self.depth and t in ('p', 'br', 'tr'):
            self.parts.append('\n')
        if t == 'a' and re.fullmatch('\\./P\\d+\\.pdf', a.get('href', '')):
            self.links.append(a['href'])

    def handle_data(self, s):
        if self.depth:
            self.parts.append(s)

    def handle_endtag(self, t):
        if t == 'div' and self.depth:
            self.depth -= 1

def beijing_food_list(keyword=''):
    p = Catalog()
    p.feed(fetch(BASE))
    if not p.items:
        raise ValueError('未识别食品监督公示列表')
    return {'source': '北京市市场监督管理局食品监督公示', 'source_url': BASE, 'items': [i for i in p.items.values() if keyword in i['title']], 'note': '仅当前首页公告标题筛选，非全国、全部历史或产品批次数据库。'}

def beijing_food_detail(path):
    matches = [i for i in beijing_food_list()['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在当前目录首页')
    url = matches[0]['url']
    p = Body()
    p.feed(fetch(url))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if not p.title or not text:
        raise ValueError('未识别公告正文')
    links = []
    for link in p.links:
        u = urljoin(url, link)
        x = urlsplit(u)
        if x.scheme == 'https' and x.hostname == 'scjgj.beijing.gov.cn' and x.path.lower().endswith(('.pdf', '.xls', '.xlsx', '.doc', '.docx')):
            links.append(quote(u, safe=':/%?=&'))
    return {'source': '北京市市场监督管理局食品监督公示', 'title': p.title, 'url': url, 'text': text, 'attachments': links, 'note': '不解析附件；检验结论针对公告所列样品和批次，需以原文为准。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(beijing_food_list(a.keyword) if a.cmd == 'list' else beijing_food_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
