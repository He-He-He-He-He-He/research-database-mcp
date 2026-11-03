"""NBS public monthly, quarterly, annual statistical reports."""
import release_runtime
from html.parser import HTMLParser
import re
import requests
BASE = 'https://data.stats.gov.cn/dg/website/publicrelease/web/external/'
KINDS = {'monthly': '1', 'quarterly': '2', 'annual': '3'}

def catalog(kind, keyword=''):
    if kind not in KINDS:
        raise ValueError('kind must be monthly, quarterly or annual')
    if not isinstance(keyword, str):
        raise ValueError('keyword must be a string')
    r = requests.get(BASE + 'queryPbLibCatalogTree', params={'code': KINDS[kind]}, timeout=30)
    r.raise_for_status()
    data = r.json().get('data')
    items = []
    if not isinstance(data, list):
        raise ValueError('invalid catalog')

    def walk(nodes, path):
        for n in nodes:
            if not isinstance(n, dict):
                continue
            name = n.get('name') or ''
            parents = path + [name]
            if n.get('type') == 'report' and re.fullmatch('[a-f0-9]{32}', str(n.get('_id', ''))):
                if keyword in ' '.join(parents):
                    items.append({'id': n['_id'], 'name': name, 'path': parents, 'report_id': n.get('report_id')})
            walk(n.get('children') or [], parents)
    walk(data, [])
    return {'source': '国家统计局国家数据', 'kind': kind, 'catalog_url': BASE + 'queryPbLibCatalogTree?code=' + KINDS[kind], 'keyword': keyword, 'items': items, 'note': '关键词仅筛选目录中的报表名称及其路径，不搜索表格内部指标；零匹配不代表相关数据不存在。'}

class _TableParser(HTMLParser):

    def __init__(self, limit, offset=0):
        super().__init__()
        self.limit = limit
        self.start_offset = offset
        self.rows = []
        self.total = 0
        self.in_row = False
        self.cell = None
        self.row = []

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.in_row = True
            self.row = []
            self.total += 1
        elif self.in_row and tag in ('td', 'th'):
            d = dict(attrs)
            self.cell = {'text': '', 'rowspan': int(d.get('rowspan', 1)), 'colspan': int(d.get('colspan', 1)), 'source_row': d.get('data-row'), 'source_col': d.get('data-col'), 'cell': d.get('data-cellhead')}
        elif tag == 'br' and self.cell is not None:
            self.cell['text'] += '\n'

    def handle_data(self, text):
        if self.cell is not None:
            self.cell['text'] += text

    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.cell is not None:
            self.cell['text'] = self.cell['text'].strip()
            self.row.append(self.cell)
            self.cell = None
        elif tag == 'tr' and self.in_row:
            if self.start_offset < self.total <= self.start_offset + self.limit:
                self.rows.append(self.row)
            self.in_row = False

def table(kind, table_id, max_rows=30, offset=0):
    if isinstance(max_rows, bool) or not isinstance(max_rows, int) or (not 1 <= max_rows <= 1000):
        raise ValueError('max_rows must be 1–1000')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 0 <= offset <= 1000000):
        raise ValueError('offset must be 0–1000000')
    items = [x for x in catalog(kind)['items'] if x['id'] == table_id]
    if len(items) != 1:
        raise ValueError('ID is not a unique report in the selected catalog')
    r = requests.get(BASE + 'new/getHtmlContentTime', params={'id': table_id}, timeout=90)
    r.raise_for_status()
    if len(r.content) > 60000000:
        raise ValueError('response too large')
    d = r.json().get('data') or {}
    html = d.get('html_content')
    if not isinstance(html, str) or '<table' not in html.lower():
        raise ValueError('official report contains no HTML table')
    p = _TableParser(max_rows, offset)
    p.feed(html)
    return {'source': '国家统计局国家数据', 'kind': kind, 'id': table_id, 'title': d.get('pblib_name') or items[0]['name'], 'path': items[0]['path'], 'metadata': {k: v for k, v in d.items() if k != 'html_content'}, 'source_url': r.url, 'total_rows': p.total, 'returned_rows': len(p.rows), 'truncated': p.total > offset + len(p.rows), 'offset': offset, 'next_offset': offset + len(p.rows) if offset + len(p.rows) < p.total else None, 'rows': p.rows, 'note': '行偏移从原表首行（包括标题、表头）起算；每次重新读取完整原表，本地切片不保证跨次更新时顺序稳定。后续片段可能缺少表头或跨越起点的合并单元格，解释数据时需同时读取表头及原始 rowspan/colspan，不可自动填零。'}
