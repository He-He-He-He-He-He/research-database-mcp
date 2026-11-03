"""北京市统计局居民消费价格指数：官方年目录、详情与 Excel 表。"""
import release_runtime
import re
import subprocess
import sys
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
BASE = 'https://tjj.beijing.gov.cn/tjsj_31433/yjdsj_31440/cpi/'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'tjj.beijing.gov.cn' or (not p.path.startswith('/tjsj_31433/yjdsj_31440/cpi/')):
        raise ValueError('仅允许访问北京市统计局 CPI 官方目录')
    return release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout

class _Links(HTMLParser):

    def __init__(self):
        super().__init__()
        self.links = []
        self._href = None
        self._text = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self._href = dict(attrs).get('href')
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag == 'a' and self._href is not None:
            self.links.append((self._href, ''.join(self._text).strip()))
            self._href = None

def list_beijing_cpi(year):
    year = int(year)
    if not 2000 <= year <= 2100:
        raise ValueError('年份超出范围')
    base = f'{BASE}{year}/'
    html = _get(base).decode('utf-8')
    match = re.search('title\\s*=\\s*"([^"]*)"\\s*;\\s*link\\s*=\\s*"([^"]*)"', html)
    if not match:
        raise ValueError('官方目录结构已变化或该年没有数据')
    dates = match.group(1).strip(';').split(';')
    links = match.group(2).strip(';').split(';')
    if len(dates) != len(links):
        raise ValueError('官方目录日期和链接数量不一致')
    return [{'directory_month': date[:7], 'directory_date': date, 'url': urljoin(base, link)} for date, link in zip(dates, links)]

def beijing_cpi_detail(url):
    html = _get(url).decode('utf-8')
    parser = _Links()
    parser.feed(html)
    attachments = [{'title': title, 'url': urljoin(url, href)} for href, title in parser.links if re.search('\\.xls$', href, re.I)]
    if not attachments:
        raise ValueError('详情没有找到 Excel 附件，可能是上游页面已变化')
    return {'url': url, 'attachments': attachments, 'note': '数据口径和调查方法请核对详情正文；目录日期与附件统计月份可能不同。'}

def beijing_cpi_table(url):
    try:
        import xlrd
    except ImportError:
        sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
        try:
            import xlrd
        except ImportError as e:
            raise RuntimeError('读取 .xls 需要先安装 xlrd：python3 -m pip install xlrd') from e
    data = _get(url)
    book = xlrd.open_workbook(file_contents=data)
    return {'url': url, 'sheets': [{'name': s.name, 'rows': [s.row_values(i) for i in range(s.nrows)]} for s in book.sheets()], 'note': '原始单元格数组，保留并列栏和完整精度；空单元格及 Excel 日期需结合表头解释。'}
