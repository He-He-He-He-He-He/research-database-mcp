"""北京市卫生健康事业发展统计公报：章节检索与正文，只读。"""
import release_runtime
import argparse, json, re, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from research import fetch
INDEX = {2025: 'https://wjw.beijing.gov.cn/sjfb/bjstjgb/bjsyjgb2025/', 2024: 'https://wjw.beijing.gov.cn/sjfb/bjstjgb/bjstjgb2024/'}

class ListParser(HTMLParser):

    def __init__(self, base):
        super().__init__()
        self.base = base
        self.url = None
        self.buf = []
        self.items = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        href = a.get('href', '')
        if tag == 'a' and re.fullmatch('\\./\\d{6}/t\\d{8}_\\d+\\.html', href):
            self.url = urljoin(self.base, href)
            self.buf = []

    def handle_data(self, s):
        if self.url:
            self.buf.append(s)

    def handle_endtag(self, tag):
        if tag == 'a' and self.url:
            self.items.append({'title': ' '.join(''.join(self.buf).split()), 'url': self.url})
            self.url = None

class DetailParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.found = False
        self.text = []
        self.title = ''
        self.table_depth = 0
        self.row = None
        self.cell = None
        self.tables = []
        self.table = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and a.get('name') == 'ArticleTitle':
            self.title = a.get('content', '')
        if not self.depth and tag == 'div' and ('TRS_UEDITOR' in a.get('class', '').split()):
            self.depth = 1
            self.found = True
            return
        if not self.depth:
            return
        if tag == 'div':
            self.depth += 1
        if tag in ('p', 'br'):
            self.text.append('\n')
        if tag == 'table':
            self.table_depth += 1
            self.table = []
        if tag == 'tr' and self.table_depth:
            self.row = []
        if tag in ('td', 'th') and self.row is not None:
            self.cell = []

    def handle_data(self, s):
        if self.depth:
            self.text.append(s)
        if self.cell is not None:
            self.cell.append(s)

    def handle_endtag(self, tag):
        if not self.depth:
            return
        if tag in ('td', 'th') and self.cell is not None:
            self.row.append(' '.join(''.join(self.cell).split()))
            self.cell = None
        if tag == 'tr' and self.row is not None:
            self.table.append(self.row)
            self.row = None
        if tag == 'table' and self.table_depth:
            self.tables.append(self.table)
            self.table_depth -= 1
        if tag == 'div':
            self.depth -= 1

def health_list(year=2025, keyword=''):
    if year not in INDEX:
        raise ValueError('目前支持 2024 和 2025 年公报')
    parser = ListParser(INDEX[year])
    parser.feed(fetch(INDEX[year]))
    if not parser.items:
        raise ValueError('未能解析公报目录，网页可能改版')
    return {'year': year, 'source_url': INDEX[year], 'items': [x for x in parser.items if keyword in x['title']], 'note': '章节标题筛选；不是逐条指标数据库。'}

def health_detail(url):
    x = urlsplit(url)
    if x.scheme != 'https' or x.netloc != 'wjw.beijing.gov.cn' or (not re.fullmatch('/sjfb/bjstjgb/(?:bjsyjgb2025|bjstjgb2024)/\\d{6}/t\\d{8}_\\d+\\.html', x.path)) or x.query or x.fragment:
        raise ValueError('仅支持本模块目录返回的公报章节链接')
    p = DetailParser()
    p.feed(fetch(url))
    if not p.found:
        raise ValueError('未找到公报正文，网页可能改版')
    return {'source_url': url, 'title': p.title, 'text': ''.join(p.text).strip(), 'tables': p.tables, 'note': '网页表格可能存在合并单元格；原始口径和注释请以官方页面为准。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('--year', type=int, default=2025)
    q.add_argument('--keyword', default='')
    q = s.add_parser('detail')
    q.add_argument('url')
    a = p.parse_args()
    print(json.dumps(health_list(a.year, a.keyword) if a.cmd == 'list' else health_detail(a.url), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
