"""国家新闻出版署游戏审批变更、撤销年度公告及表格。"""
import release_runtime
import re, subprocess
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
ROOT = 'https://www.nppa.gov.cn/bsfw/jggs/yxspjg/'
KINDS = {'变更': 'yxspbgxx', '撤销': 'yxspcxxx'}

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.nppa.gov.cn' or (not p.path.startswith('/bsfw/jggs/yxspjg/')) or p.query or p.fragment:
        raise ValueError('仅支持新闻出版署游戏审批公告')
    return release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '25', '--max-redirs', '0', url], check=True, capture_output=True).stdout.decode('utf-8-sig')

class _Notices(HTMLParser):

    def __init__(self, base):
        super().__init__()
        self.base = base
        self.in_ul = False
        self.li = None
        self.anchor = False
        self.in_span = False
        self.rows = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'ul' and 'm2nrul' in a.get('class', '').split():
            self.in_ul = True
        elif self.in_ul and tag == 'li':
            self.li = {'title': '', 'url': '', 'date': ''}
        elif self.li is not None and tag == 'a' and (not self.li['url']):
            self.li['url'] = urljoin(self.base, a.get('href', ''))
            self.anchor = True
        elif self.li is not None and tag == 'span':
            self.in_span = True

    def handle_data(self, data):
        if self.li is not None and self.in_span:
            self.li['date'] += data
        elif self.li is not None and self.anchor:
            match = re.search('>([^<>]*游戏审批[^<>]*信息)</a>', data)
            if match:
                self.li['title'] = match.group(1)
            elif 'var _docTitle' not in data:
                self.li['title'] += data

    def handle_endtag(self, tag):
        if tag == 'a':
            self.anchor = False
        elif tag == 'span':
            self.in_span = False
        elif tag == 'li' and self.li is not None:
            r = {k: v.strip().strip('[]') for k, v in self.li.items()}
            if r['url'] and r['title']:
                self.rows.append(r)
            self.li = None
        elif tag == 'ul' and self.in_ul:
            self.in_ul = False

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

    def handle_data(self, text):
        if self.cell is not None:
            self.cell.append(text)

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

def nppa_game_change_notices(kind='变更', page=1):
    if kind not in KINDS:
        raise ValueError('kind 仅支持变更或撤销')
    page = int(page)
    if not 1 <= page <= 100:
        raise ValueError('页码必须在 1—100')
    base = ROOT + KINDS[kind] + '/'
    url = base if page == 1 else urljoin(base, f'index_{page - 1}.html')
    p = _Notices(base)
    p.feed(_get(url))
    if not p.rows:
        raise ValueError('栏目无记录或网页结构变化')
    return p.rows

def nppa_game_change_table(url, keyword='', page=1, page_size=20):
    p = urlparse(url)
    if not re.fullmatch('/bsfw/jggs/yxspjg/(?:yxspbgxx|yxspcxxx)/\\d{6}/t\\d{8}_\\d+\\.html', p.path):
        raise ValueError('仅支持游戏变更、撤销公告详情')
    page = int(page)
    page_size = int(page_size)
    if page < 1 or not 1 <= page_size <= 100:
        raise ValueError('页码须大于零，每页 1—100 条')
    parser = _Tables()
    parser.feed(_get(url))
    tables = [t for t in parser.tables if t and '序号' in t[0] and ('名称' in t[0]) and ('变更信息' in t[0] or '撤销信息' in t[0])]
    if len(tables) != 1:
        raise ValueError('未能唯一识别公告表格')
    head = tables[0][0]
    rows = []
    for i, row in enumerate(tables[0][1:], 1):
        if len(row) != len(head) or not row[0].isdigit() or int(row[0]) != i:
            raise ValueError('表格行列或序号异常')
        rows.append(dict(zip(head, row)))
    needle = ''.join(keyword.split()).casefold()
    matched = [r for r in rows if needle in ''.join((''.join(str(v).split()) for v in r.values())).casefold()]
    return {'url': url, 'source_total': len(rows), 'filtered_total': len(matched), 'page': page, 'page_size': page_size, 'results': matched[(page - 1) * page_size:page * page_size]}
