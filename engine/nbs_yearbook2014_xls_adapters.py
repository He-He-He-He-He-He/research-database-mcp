"""中国统计年鉴 2014 目录和官方 XLS 原表。"""
import release_runtime
import argparse
from html.parser import HTMLParser
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urljoin, urlsplit
BASE = 'https://www.stats.gov.cn/sj/ndsj/2014/'
INDEX = BASE + 'left.htm'
PATH = re.compile('/sj/ndsj/2014/zk/html/[A-Za-z0-9_-]{1,80}\\.[hH][tT][mM]')

def _get(url):
    result = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], check=True, capture_output=True)
    if len(result.stdout) > 32 * 1024 * 1024:
        raise ValueError('文件超过 32 MiB 上限')
    return result.stdout

class _Catalog(HTMLParser):

    def __init__(self):
        super().__init__()
        self.active = None
        self.parts = []
        self.items = {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'a' and a.get('href'):
            url = urljoin(BASE, a['href'])
            u = urlsplit(url)
            if u.scheme == 'https' and u.netloc == 'www.stats.gov.cn' and PATH.fullmatch(u.path):
                self.active = url
                self.parts = []

    def handle_data(self, text):
        if self.active is not None:
            self.parts.append(text)

    def handle_endtag(self, tag):
        if tag == 'a' and self.active is not None:
            title = ' '.join(''.join(self.parts).split())
            if title:
                self.items[self.active] = {'title': title, 'url': self.active}
            self.active = None

class _XlsLink(HTMLParser):

    def __init__(self, page_url):
        super().__init__()
        self.page_url = page_url
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag != 'a':
            return
        href = dict(attrs).get('href', '').strip()
        if re.fullmatch('[A-Za-z0-9_-]+\\.xls', href, re.I):
            self.links.append(urljoin(self.page_url, href))

def yearbook2014_catalog(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 80:
        raise ValueError('关键词须不超过 80 字符')
    p = _Catalog()
    p.feed(_get(INDEX).decode('gb18030'))
    if not p.items:
        raise ValueError('未读取统计年鉴目录')
    items = [x for x in p.items.values() if keyword in x['title']]
    return {'source_url': INDEX, 'yearbook': '中国统计年鉴2014', 'total': len(p.items), 'matched_count': len(items), 'items': items, 'note': 'total 为全目录数，matched_count 为标题关键词命中数；仅目录中的 HTML 页面，并非所有页面都提供 XLS。表中年份和口径各异。'}

def yearbook2014_table(url):
    u = urlsplit(url)
    if u.scheme != 'https' or u.netloc != 'www.stats.gov.cn' or u.query or u.fragment or (not PATH.fullmatch(u.path)):
        raise ValueError('仅接受 2014 年鉴 zk/html 下的官方 HTML 页面')
    try:
        import xlrd
    except ImportError:
        sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
        try:
            import xlrd
        except ImportError as exc:
            raise RuntimeError('XLS 解析需要 xlrd：python3 -m pip install xlrd') from exc
    p = _XlsLink(url)
    p.feed(_get(url).decode('gb18030'))
    links = list(dict.fromkeys(p.links))
    if len(links) != 1:
        raise ValueError('页面无唯一 XLS 原表链接')
    xls_url = links[0]
    x = urlsplit(xls_url)
    if x.scheme != 'https' or x.netloc != 'www.stats.gov.cn' or (not re.fullmatch('/sj/ndsj/2014/zk/html/[A-Za-z0-9_-]{1,80}\\.xls', x.path, re.I)):
        raise ValueError('XLS 链接不在允许的年鉴目录')
    book = xlrd.open_workbook(file_contents=_get(xls_url), formatting_info=True)
    sheets = []
    for sh in book.sheets():
        if sh.nrows > 5000 or sh.ncols > 300:
            raise ValueError('表格超出安全尺寸')
        rows = []
        for r in range(sh.nrows):
            rows.append([{'value': sh.cell_value(r, c), 'cell_type': sh.cell_type(r, c)} for c in range(sh.ncols)])
        sheets.append({'name': sh.name, 'rows': rows, 'merged_ranges': [{'start_row': a + 1, 'end_row': b, 'start_col': c + 1, 'end_col': d} for a, b, c, d in sh.merged_cells]})
    return {'source_page_url': url, 'source_xls_url': xls_url, 'yearbook': '中国统计年鉴2014', 'sheets': sheets, 'note': '原始 XLS 数值可能包含显示格式隐藏的小数，未按表格显示精度四舍五入；保留空白单元格、数据类型和合并范围，不把空白当零。数据年份、调查范围和单位请核对原表。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('catalog')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('table')
    q.add_argument('url')
    a = p.parse_args()
    print(json.dumps(yearbook2014_catalog(a.keyword) if a.cmd == 'catalog' else yearbook2014_table(a.url), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
