"""国家电影局历年电影发行经营许可证公示名单。"""
import release_runtime
import re, subprocess
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
BASE = 'https://www.chinafilm.gov.cn/xxgk/gsxx/dyfxjyxkz/'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.chinafilm.gov.cn' or (not p.path.startswith('/xxgk/gsxx/dyfxjyxkz/')) or p.query or p.fragment:
        raise ValueError('仅支持国家电影局电影发行经营许可证栏目')
    return release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '25', '--max-redirs', '0', url], check=True, capture_output=True).stdout.decode('utf-8-sig')

class _List(HTMLParser):

    def __init__(self):
        super().__init__()
        self.item = None
        self.anchor = False
        self.date = False
        self.rows = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'a' and 'm2r_a' in a.get('class', '').split():
            self.item = {'url': urljoin(BASE, a.get('href', '')), 'title': ''}
            self.anchor = True
        elif tag == 'span' and self.item is not None and (not self.anchor):
            self.date = True
            self.item['date'] = ''

    def handle_data(self, text):
        if self.anchor:
            self.item['title'] += text
        elif self.date:
            self.item['date'] += text

    def handle_endtag(self, tag):
        if tag == 'a' and self.anchor:
            self.anchor = False
        elif tag == 'span' and self.date:
            self.date = False
        elif tag == 'li' and self.item is not None:
            r = {k: v.strip().lstrip('•').strip() for k, v in self.item.items()}
            self.rows.append(r)
            self.item = None

class _Tables(HTMLParser):

    def __init__(self):
        super().__init__()
        self.table = None
        self.row = None
        self.cell = None
        self.tables = []

    def handle_starttag(self, tag, attrs):
        if tag == 'table' and self.table is None:
            self.table = []
        elif tag == 'tr' and self.table is not None:
            self.row = []
        elif tag in ('td', 'th') and self.row is not None:
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.cell is not None:
            self.row.append(' '.join(''.join(self.cell).split()))
            self.cell = None
        elif tag == 'tr' and self.row is not None:
            self.table.append(self.row)
            self.row = None
        elif tag == 'table' and self.table is not None:
            self.tables.append(self.table)
            self.table = None

def film_distributor_notices(page=1):
    page = int(page)
    if not 1 <= page <= 100:
        raise ValueError('页码必须在 1—100')
    url = BASE if page == 1 else urljoin(BASE, f'index_{page - 1}.html')
    p = _List()
    p.feed(_get(url))
    if not p.rows:
        raise ValueError('未发现名单目录，页码或站点结构有变化')
    return p.rows

def film_distributors(url, keyword='', page=1, page_size=20):
    p = urlparse(url)
    if not re.fullmatch('/xxgk/gsxx/dyfxjyxkz/\\d{6}/t\\d{8}_\\d+\\.html', p.path):
        raise ValueError('仅支持发行经营许可证公示名单详情')
    page = int(page)
    page_size = int(page_size)
    if page < 1 or not 1 <= page_size <= 100:
        raise ValueError('页码必须大于 0，每页 1—100 条')
    parser = _Tables()
    parser.feed(_get(url))
    tables = [t for t in parser.tables if t and len(t[0]) >= 3 and ('序号' in t[0][0]) and ('证号' in t[0][1]) and ('公司' in t[0][2])]
    if len(tables) != 1:
        raise ValueError('无法唯一识别名单表')
    rows = []
    for row in tables[0][1:]:
        if len(row) < 3 or not row[0].strip().isdigit():
            raise ValueError('发现非预期表格行，未猜测处理')
        rows.append({'序号': int(row[0]), '证号': row[1], '公司名称': row[2]})
    if not rows or [r['序号'] for r in rows] != list(range(1, len(rows) + 1)):
        raise ValueError('名单序号不连续')
    needle = ''.join(keyword.split()).casefold()
    matched = [r for r in rows if needle in ''.join((''.join(str(v).split()) for v in r.values())).casefold()]
    return {'url': url, 'source_total': len(rows), 'filtered_total': len(matched), 'page': page, 'page_size': page_size, 'results': matched[(page - 1) * page_size:page * page_size]}
