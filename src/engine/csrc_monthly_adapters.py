"""中国证监会证券市场月报目录和附件地址，只读。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, quote
BASE = 'https://www.csrc.gov.cn'
INDEX = BASE + '/csrc/c100120/common_list.shtml'

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
        if t == 'a' and re.fullmatch('/csrc/c100120/c\\d+/content\\.shtml', h):
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

class Attachments(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.links = []

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'div':
            if self.depth:
                self.depth += 1
            elif a.get('id') == 'files':
                self.depth = 1
        if self.depth and t == 'a' and a.get('href'):
            self.links.append(a['href'])

    def handle_endtag(self, t):
        if t == 'div' and self.depth:
            self.depth -= 1

def csrc_monthly_list(keyword='', *, page=1):
    if type(page) is not int or not 1 <= page <= 100:
        raise ValueError('page 须为1至100')
    url = INDEX if page == 1 else INDEX.replace('common_list.shtml', f'common_list_{page}.shtml')
    p = Catalog()
    p.feed(fetch(url))
    if not p.items:
        raise ValueError('未识别证券市场月报列表')
    return {'source': '中国证监会证券市场月报', 'source_url': url, 'page': page, 'items': [i for i in p.items.values() if keyword in i['title']], 'note': '仅当前官方列表页按标题筛选，非全站、全部历史或行情 API；来源页码及内容可能随更新变化。'}

def csrc_monthly_detail(path, *, page=1):
    matches = [i for i in csrc_monthly_list(page=page)['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在指定目录页')
    url = matches[0]['url']
    p = Attachments()
    p.feed(fetch(url))
    links = []
    for link in p.links:
        u = urljoin(url, link)
        x = urlsplit(u)
        if x.scheme == 'https' and x.hostname == 'www.csrc.gov.cn' and x.path.lower().endswith(('.doc', '.docx', '.pdf', '.xls', '.xlsx')):
            links.append(quote(u, safe=':/%?=&'))
    if not links:
        raise ValueError('未识别月报附件')
    return {'source': '中国证监会证券市场月报', **matches[0], 'attachments': links, 'note': '仅返回官方附件地址，未解析或转换；扩展名可能与实际文件格式不一致。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q.add_argument('--page', type=int, default=1)
    q = s.add_parser('detail')
    q.add_argument('path')
    q.add_argument('--page', type=int, default=1)
    a = p.parse_args()
    print(json.dumps(csrc_monthly_list(a.keyword, page=a.page) if a.cmd == 'list' else csrc_monthly_detail(a.path, page=a.page), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
