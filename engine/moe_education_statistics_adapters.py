"""教育部全国教育统计公开表格。"""
import release_runtime
import re
import subprocess
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from szse_chinext_adapters import _Links
BASE = 'https://www.moe.gov.cn/jyb_sjzl/moe_560/'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.moe.gov.cn' or (not p.path.startswith('/jyb_sjzl/moe_560/')):
        raise ValueError('仅允许教育部教育统计数据栏目')
    return release_runtime.run(['curl', '--location', '--max-redirs', '3', '--proto-redir', '=http,https', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout.decode('utf-8')

def moe_education_list(year=2024, page=1):
    year = int(year)
    page = int(page)
    if not 2000 <= year <= 2100 or not 1 <= page <= 100:
        raise ValueError('年份或页码超出范围')
    base = f'{BASE}{year}/quanguo/'
    p = _Links()
    p.feed(_get(base if page == 1 else urljoin(base, f'index_{page - 1}.html')))
    items = []
    for href, title in p.links:
        url = urljoin(base, href)
        if re.fullmatch(re.escape(base) + '\\d{6}/t\\d{8}_\\d+\\.html', url) and title:
            items.append({'title': title, 'url': url})
    if not items:
        raise ValueError('未找到表格目录，可能该年或该页不存在、网站改版')
    return items

class _LeafTables(HTMLParser):

    def __init__(self):
        super().__init__()
        self.stack = []
        self.tables = []

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            if self.stack:
                self.stack[-1]['nested'] = True
            self.stack.append({'rows': [], 'row': None, 'cell': None, 'nested': False})
        elif self.stack:
            cur = self.stack[-1]
            if tag == 'tr':
                cur['row'] = []
            elif tag in ('td', 'th') and cur['row'] is not None:
                cur['cell'] = {'text': '', 'rowspan': dict(attrs).get('rowspan', '1'), 'colspan': dict(attrs).get('colspan', '1')}

    def handle_data(self, data):
        if self.stack and self.stack[-1]['cell'] is not None:
            self.stack[-1]['cell']['text'] += data

    def handle_endtag(self, tag):
        if not self.stack:
            return
        cur = self.stack[-1]
        if tag in ('td', 'th') and cur['cell'] is not None:
            cur['cell']['text'] = ' '.join(cur['cell']['text'].split())
            cur['row'].append(cur['cell'])
            cur['cell'] = None
        elif tag == 'tr' and cur['row'] is not None:
            cur['rows'].append(cur['row'])
            cur['row'] = None
        elif tag == 'table':
            t = self.stack.pop()
            if not t['nested'] and t['rows']:
                self.tables.append(t['rows'])

def moe_education_table(url):
    p = _LeafTables()
    p.feed(_get(url))
    if not p.tables:
        raise ValueError('未解析到表格')
    return {'url': url, 'tables': p.tables, 'note': '只返回叶级表格，保留合并单元格属性；统计分类、口径与排除范围请核对原文。'}
