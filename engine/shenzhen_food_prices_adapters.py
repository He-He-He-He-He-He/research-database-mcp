"""深圳发改委重要食品价格月报和 DOCX 均价表。"""
import release_runtime
import io
import re
import subprocess
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
BASE = 'https://fgw.sz.gov.cn/zwgk/zdlyxxgkzl/zyspjgjcyb/'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'fgw.sz.gov.cn' or (not (p.path.startswith('/zwgk/zdlyxxgkzl/zyspjgjcyb/') or p.path.startswith('/attachment/'))):
        raise ValueError('仅允许深圳发改委食品价格月报及官方附件')
    return release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout

class _Links(HTMLParser):

    def __init__(self):
        super().__init__()
        self.href = None
        self.text = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.href = dict(attrs).get('href')
            self.text = []

    def handle_data(self, data):
        if self.href is not None:
            self.text.append(data)

    def handle_endtag(self, tag):
        if tag == 'a' and self.href is not None:
            self.links.append((self.href, ' '.join(''.join(self.text).split())))
            self.href = None

def list_shenzhen_food_reports():
    p = _Links()
    p.feed(_get(urljoin(BASE, 'index.html')).decode('utf-8'))
    return [{'title': title, 'url': urljoin(BASE, href)} for href, title in p.links if '/zyspjgjcyb/content/post_' in href and title]

def shenzhen_food_report(url):
    p = _Links()
    p.feed(_get(url).decode('utf-8'))
    attachments = [{'title': title, 'url': urljoin(url, href)} for href, title in p.links if re.search('\\.docx$', href, re.I)]
    if not attachments:
        raise ValueError('详情未发现 DOCX 附件，该月可能仅发布文字，或页面结构已变化')
    return {'url': url, 'attachments': attachments}

def shenzhen_food_table(url):
    try:
        from docx import Document
    except ImportError as e:
        raise RuntimeError('读取 Word 表格需要安装 python-docx') from e
    doc = Document(io.BytesIO(_get(url)))
    tables = [[[cell.text for cell in row.cells] for row in table.rows] for table in doc.tables]
    if not tables:
        raise ValueError('附件中没有表格')
    return {'url': url, 'tables': tables, 'note': '保留文字和单位，Word 合并单元格可能在每个网格位置重复，请核对原始表格。'}
