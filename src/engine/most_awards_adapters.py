"""科技部政务服务平台首页公开通知及科技奖项目目录。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
BASE = 'https://fuwu.most.gov.cn'
INDEX = BASE + '/'

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
        if t == 'a' and title and re.fullmatch('/html/tztg/xzxkzx/\\d{8}/\\d+\\.html', h):
            self.items[h] = {'path': h, 'title': title, 'url': BASE + h}

class Body(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.parts = []
        self.rows = []
        self.row = None
        self.cell = None

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'div':
            if self.depth:
                self.depth += 1
            elif a.get('id') == 'xp_zw':
                self.depth = 1
        if self.depth and t in ('p', 'br', 'tr'):
            self.parts.append('\n')
        if self.depth and t == 'tr':
            self.row = []
        if self.depth and self.row is not None and (t in ('td', 'th')):
            self.cell = []

    def handle_data(self, s):
        if self.depth:
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
        if t == 'div' and self.depth:
            self.depth -= 1

def most_service_list(keyword=''):
    p = Catalog()
    p.feed(fetch(INDEX))
    if not p.items:
        raise ValueError('未识别科技部服务平台首页通知')
    return {'source': '科技部政务服务平台首页通知', 'source_url': INDEX, 'items': [i for i in p.items.values() if keyword in i['title']], 'note': '只筛选首页列出的通知，不是全站或全部获奖项目搜索。'}

def most_service_detail(path):
    matches = [i for i in most_service_list()['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在当前首页')
    p = Body()
    p.feed(fetch(matches[0]['url']))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if not text:
        raise ValueError('未识别通知正文')
    return {'source': '科技部政务服务平台首页通知', **matches[0], 'text': text, 'table_rows': p.rows, 'note': '表格保留源文顺序与单元格，未重建合并单元格；仅该项通知的数据，请核对原文。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(most_service_list(a.keyword) if a.cmd == 'list' else most_service_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
