"""深圳证券交易所创业板市场统计月报：目录、章节、原始表格。"""
import release_runtime
import re
import subprocess
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
BASE = 'https://www.szse.cn/certificate/secondb/GEMmsb/'
TABLE_PREFIX = '/www/certificate/secondb/GEMmsb/'

def _get(url):
    p = urlparse(url)
    valid = p.scheme == 'https' and (p.hostname == 'www.szse.cn' and p.path.startswith('/certificate/secondb/GEMmsb/') or (p.hostname == 'docs.static.szse.cn' and p.path.startswith(TABLE_PREFIX)))
    if not valid:
        raise ValueError('仅允许读取深交所创业板月报目录及表格')
    return release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout

def list_chinext_reports(page=1):
    page = int(page)
    if page < 1 or page > 100:
        raise ValueError('页码超出范围')
    url = BASE if page == 1 else urljoin(BASE, f'index_{page - 1}.html')
    html = _get(url).decode('utf-8')
    pattern = "var\\s+curHref\\s*=\\s*'([^']+)'\\s*;(?:(?!var\\s+curHref).)*?\\bvar\\s+curTitle\\s*=\\s*'([^']+)'"
    found = re.findall(pattern, html, flags=re.S)
    return [{'title': title, 'url': urljoin(BASE, href)} for href, title in found if '创业板市场统计月报' in title]

class _Links(HTMLParser):

    def __init__(self):
        super().__init__()
        self.href = None
        self.parts = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.href = dict(attrs).get('href')
            self.parts = []

    def handle_data(self, data):
        if self.href is not None:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == 'a' and self.href is not None:
            self.links.append((self.href, ''.join(self.parts).strip()))
            self.href = None

def chinext_report_sections(url):
    html = _get(url).decode('utf-8')
    parser = _Links()
    parser.feed(html)
    sections = []
    for href, title in parser.links:
        p = urlparse(href)
        if p.hostname == 'docs.static.szse.cn' and p.path.startswith(TABLE_PREFIX) and p.path.endswith('.html'):
            sections.append({'title': title, 'url': 'https://docs.static.szse.cn' + p.path})
    if not sections:
        raise ValueError('未找到统计章节，上游页面结构可能变化')
    return sections

class _Tables(HTMLParser):

    def __init__(self):
        super().__init__()
        self.tables = []
        self.table = None
        self.row = None
        self.cell = None

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

def chinext_section_table(url):
    data = _get(url)
    parser = _Tables()
    parser.feed(data.decode('gb18030'))
    if not parser.tables:
        raise ValueError('未找到 HTML 表格，上游页面结构可能变化')
    return {'url': url, 'tables': parser.tables, 'note': '原始行和单元格，单位、表头、跨行跨列请对照原始网页。'}
