"""国家统计局最新数据发布栏目。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urljoin
BASE = 'https://www.stats.gov.cn/sj/zxfb/'

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
        self.skip = 0
        self.parts = []
        self.rows = []
        self.row = None
        self.cell = None
        self.title = ''

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'meta' and a.get('name') == 'ArticleTitle':
            self.title = a.get('content', '')
        if t == 'div':
            if self.depth:
                self.depth += 1
            elif 'TRS_UEDITOR' in a.get('class', '').split():
                self.depth = 1
        if self.depth and t in ('style', 'script'):
            self.skip += 1
        if self.depth and (not self.skip) and (t in ('p', 'br', 'tr')):
            self.parts.append('\n')
        if self.depth and t == 'tr':
            self.row = []
        if self.depth and self.row is not None and (t in ('td', 'th')):
            self.cell = []

    def handle_data(self, s):
        if self.depth and (not self.skip):
            self.parts.append(s)
        if self.cell is not None:
            self.cell.append(s)

    def handle_endtag(self, t):
        if self.depth and t in ('td', 'th') and (self.cell is not None):
            self.row.append(' '.join(''.join(self.cell).split()))
            self.cell = None
        if self.depth and t == 'tr' and (self.row is not None):
            self.rows.append(self.row)
            self.row = None
        if self.depth and t in ('style', 'script') and self.skip:
            self.skip -= 1
        if self.depth and t == 'div':
            self.depth -= 1

def stats_releases(keyword=''):
    p = Catalog()
    p.feed(fetch(BASE))
    if not p.items:
        raise ValueError('未识别最新数据发布列表')
    return {'source': '国家统计局最新数据发布', 'source_url': BASE, 'items': [i for i in p.items.values() if keyword in i['title']], 'note': '只筛选当前首页，非全站或历史全量搜索。'}

def stats_release_detail(path):
    matches = [i for i in stats_releases()['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在当前首页')
    p = Body()
    p.feed(fetch(matches[0]['url']))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if not p.title or not text:
        raise ValueError('未识别统计发布正文')
    return {'source': '国家统计局最新数据发布', 'title': p.title, 'url': matches[0]['url'], 'text': text, 'table_rows': p.rows, 'note': '表格保留原行单元格，不重建合并单元格；指标、单位与统计方法请核对原文。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(stats_releases(a.keyword) if a.cmd == 'list' else stats_release_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
