"""国家发改委公开的国家粮储局粮食收购数据。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urljoin
BASE = 'https://www.ndrc.gov.cn/fgsj/tjsj/lslt/shougoushuju/'

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
        self.source = ''

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'meta' and a.get('name') == 'ArticleTitle':
            self.title = a.get('content', '')
        if t == 'meta' and a.get('name') == 'ContentSource':
            self.source = a.get('content', '')
        if t == 'div':
            if self.depth:
                self.depth += 1
            elif 'article_con_title' in a.get('class', '').split():
                self.depth = 1
        if self.depth and t in ('p', 'br', 'tr'):
            self.parts.append('\n')

    def handle_data(self, s):
        if self.depth:
            self.parts.append(s)

    def handle_endtag(self, t):
        if t == 'div' and self.depth:
            self.depth -= 1

def grain_procurement_list(keyword=''):
    p = Catalog()
    p.feed(fetch(BASE))
    if not p.items:
        raise ValueError('未识别粮食收购目录')
    return {'source': '国家发改委公开粮食收购数据', 'source_url': BASE, 'items': [i for i in p.items.values() if keyword in i['title']], 'note': '仅筛选当前首页标题，非粮食交易、价格或历史全量数据库。'}

def grain_procurement_detail(path):
    matches = [i for i in grain_procurement_list()['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在当前首页')
    p = Body()
    p.feed(fetch(matches[0]['url']))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if not p.title or not text:
        raise ValueError('未识别正文')
    return {'source': '国家发改委公开粮食收购数据', 'original_source': p.source, 'title': p.title, 'url': matches[0]['url'], 'text': text, 'note': '文字摘自原文，时间、计量单位及统计范围须核对官方原文。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(grain_procurement_list(a.keyword) if a.cmd == 'list' else grain_procurement_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
