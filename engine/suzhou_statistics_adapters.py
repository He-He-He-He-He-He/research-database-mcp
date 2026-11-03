"""苏州市统计局进度数据目录和官方表格。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urlencode
BASE = 'https://tjj.suzhou.gov.cn'
INDEX = BASE + '/sztjj/jdsj/nav_jdsj.shtml'
QUERY = BASE + '/szsfront/tjj/jdsj.jsp?'

def fetch(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True)
    if p.returncode:
        raise RuntimeError('上游请求失败（curl 状态 %d）' % p.returncode)
    return p.stdout.decode('utf-8')

class Catalog(HTMLParser):

    def __init__(self):
        super().__init__()
        self.in_table = False
        self.row = None
        self.cell = None
        self.link = None
        self.items = []
        self.in_option = False
        self.opt = None
        self.opttext = []
        self.years = {}

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'option' and a.get('value'):
            self.in_option = True
            self.opt = a['value']
            self.opttext = []
        if t == 'tbody' and a.get('id') == 'monthList':
            self.in_table = True
        if self.in_table and t == 'tr':
            self.row = []
        if self.in_table and self.row is not None and (t == 'td'):
            self.cell = []
            self.link = None
        if self.cell is not None and t == 'a':
            self.link = a.get('href')

    def handle_data(self, s):
        if self.in_option:
            self.opttext.append(s)
        if self.cell is not None:
            self.cell.append(s)

    def handle_endtag(self, t):
        if t == 'option' and self.in_option:
            year = ''.join(self.opttext).strip().removesuffix('年')
            if re.fullmatch('\\d{4}', year) and re.fullmatch('[0-9a-f]{32}', self.opt):
                self.years[year] = self.opt
            self.in_option = False
        if self.in_table and t == 'td' and (self.cell is not None):
            self.row.append((' '.join(''.join(self.cell).split()), self.link))
            self.cell = None
        if self.in_table and t == 'tr' and (self.row is not None):
            if self.row:
                name = self.row[0][0]
                for month, path in self.row[1:]:
                    if path and re.fullmatch('/sztjj/jdsj/\\d{6}/[0-9a-f]{32}\\.shtml', path) and month.isdigit():
                        self.items.append({'indicator': name, 'month': int(month), 'path': path, 'url': BASE + path})
            self.row = None
        if t == 'tbody' and self.in_table:
            self.in_table = False

class Table(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.parts = []
        self.row = None
        self.cell = None
        self.rows = []
        self.title = ''

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'meta' and a.get('name') == 'ArticleTitle':
            self.title = a.get('content', '')
        if t == 'div':
            if self.depth:
                self.depth += 1
            elif a.get('id') == 'zoom':
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
        if self.depth and t == 'div':
            self.depth -= 1

def suzhou_statistics(keyword='', year=2026):
    html = fetch(INDEX)
    m = re.search('/szsfront/tjj/jdsj\\.jsp\\?year=([0-9a-f]{32})', html)
    if not m:
        raise ValueError('未识别进度数据入口')
    first = Catalog()
    first.feed(fetch(QUERY + urlencode({'year': m.group(1)})))
    key = first.years.get(str(year))
    if not key:
        raise ValueError('年份不在官方选项中')
    p = first if key == m.group(1) else Catalog()
    if p is not first:
        p.feed(fetch(QUERY + urlencode({'year': key})))
    if not p.items:
        raise ValueError('未识别进度指标列表')
    return {'source': '苏州市统计局进度数据', 'source_url': INDEX, 'year': year, 'items': [i for i in p.items if keyword in i['indicator']], 'note': '按指定年份指标名称筛选；月份来自目录，数据口径以详情为准。'}

def suzhou_statistic_detail(path, year=2026):
    matches = [i for i in suzhou_statistics('', year)['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在所选年度目录')
    p = Table()
    p.feed(fetch(matches[0]['url']))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if not p.title or not p.rows:
        raise ValueError('未识别官方表格')
    return {'source': '苏州市统计局进度数据', 'year': year, **matches[0], 'title': p.title, 'text': text, 'table_rows': p.rows, 'note': '原表按行读取，不重建合并单元格、自动解释指数基期或缺失值；核对原文。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q.add_argument('--year', type=int, default=2026)
    q = s.add_parser('detail')
    q.add_argument('path')
    q.add_argument('--year', type=int, default=2026)
    a = p.parse_args()
    print(json.dumps(suzhou_statistics(a.keyword, a.year) if a.cmd == 'list' else suzhou_statistic_detail(a.path, a.year), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
