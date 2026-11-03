"""上海市统计局公开月度统计：目录和表格，只读。"""
import release_runtime
import argparse, json, re, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from research import fetch
BASE = 'https://tjj.sh.gov.cn/ydsj/index.html'

class Index(HTMLParser):

    def __init__(self):
        super().__init__()
        self.items = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        href = a.get('href', '')
        title = a.get('title', '')
        if tag == 'a' and 'a1' in a.get('class', '').split() and title and re.fullmatch('/ydsj\\d+/\\d{8}/[a-f0-9]{32}\\.html', href):
            self.items.append({'title': title, 'url': urljoin(BASE, href)})

class Article(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.found = False
        self.title = ''
        self.table = None
        self.row = None
        self.cell = None
        self.tables = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and a.get('name') == 'ArticleTitle':
            self.title = a.get('content', '')
        if not self.depth and tag == 'div' and (a.get('id') == 'ivs_content'):
            self.depth = 1
            self.found = True
            return
        if not self.depth:
            return
        if tag == 'div':
            self.depth += 1
        if tag == 'table':
            self.table = []
        if tag == 'tr' and self.table is not None:
            self.row = []
        if tag in ('td', 'th') and self.row is not None:
            self.cell = {'text': '', 'rowspan': a.get('rowspan', '1'), 'colspan': a.get('colspan', '1')}

    def handle_data(self, s):
        if self.cell is not None:
            self.cell['text'] += s

    def handle_endtag(self, tag):
        if not self.depth:
            return
        if tag in ('td', 'th') and self.cell is not None:
            self.cell['text'] = ' '.join(self.cell['text'].split())
            self.row.append(self.cell)
            self.cell = None
        if tag == 'tr' and self.row is not None:
            self.table.append(self.row)
            self.row = None
        if tag == 'table' and self.table is not None:
            self.tables.append(self.table)
            self.table = None
        if tag == 'div':
            self.depth -= 1

def shanghai_list(keyword=''):
    p = Index()
    p.feed(fetch(BASE))
    if not p.items:
        raise ValueError('未解析到月度统计目录，可能网站改版')
    return {'source_url': BASE, 'scope': '当前页面提供的年度月度表格目录', 'items': [x for x in p.items if keyword in x['title']], 'note': '按当前目录标题筛选；不包括其他页面全部历史数据。'}

def shanghai_detail(url):
    x = urlsplit(url)
    if x.scheme != 'https' or x.netloc != 'tjj.sh.gov.cn' or (not re.fullmatch('/ydsj\\d+/\\d{8}/[a-f0-9]{32}\\.html', x.path)) or x.query or x.fragment:
        raise ValueError('只接受本模块目录返回的上海统计月度表格链接')
    p = Article()
    p.feed(fetch(url))
    if not p.found or not p.tables:
        raise ValueError('未识别到统计表格，可能是页面改版或该条无表格')
    return {'source_url': url, 'title': p.title, 'tables': p.tables, 'note': '保留 rowspan 和 colspan；空白单元格及统计口径请核对官方原表。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('--keyword', default='')
    q = s.add_parser('detail')
    q.add_argument('url')
    a = p.parse_args()
    print(json.dumps(shanghai_list(a.keyword) if a.cmd == 'list' else shanghai_detail(a.url), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
