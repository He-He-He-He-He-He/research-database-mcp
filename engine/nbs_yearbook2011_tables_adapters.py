"""中国统计年鉴 2011 年可解析 HTML 目录与原表。"""
import release_runtime
import argparse
from html.parser import HTMLParser
import json
import re
import subprocess
from urllib.parse import urljoin, urlsplit
from moe_education_statistics_adapters import _LeafTables
BASE = 'https://www.stats.gov.cn/sj/ndsj/2011/'
INDEX = BASE + 'left.htm'
PATH = re.compile('/sj/ndsj/2011/html/[A-Za-z0-9_-]{1,80}\\.[hH][tT][mM]')

def _get(url):
    b = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], check=True, capture_output=True).stdout
    return b.decode('gb18030')

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

def yearbook2011_catalog(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 80:
        raise ValueError('关键词须不超过 80 字符')
    p = _Catalog()
    p.feed(_get(INDEX))
    if not p.items:
        raise ValueError('未读取统计年鉴目录')
    items = [x for x in p.items.values() if keyword in x['title']]
    return {'source_url': INDEX, 'yearbook': '中国统计年鉴2011', 'total': len(p.items), 'matched_count': len(items), 'items': items, 'note': 'total 为全目录数，matched_count 为标题关键词命中数；表格年份与定义各异，不等于均为2011年的数据。'}

def yearbook2011_table(url):
    u = urlsplit(url)
    if u.scheme != 'https' or u.netloc != 'www.stats.gov.cn' or u.query or u.fragment or (not PATH.fullmatch(u.path)):
        raise ValueError('仅接受 2011 年鉴目录下的官方 HTML 页面地址')
    p = _LeafTables()
    p.feed(_get(url))
    if not p.tables:
        raise ValueError('未识别 HTML 表；该页面可能是正文说明而不是数据表')
    return {'source_url': url, 'yearbook': '中国统计年鉴2011', 'tables': p.tables, 'note': '保留原始表名、单位、表头和合并单元格；年份/单位可能分行列，空白不能补零，数据来源和统计口径请核对章节说明与原文。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('catalog')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('table')
    q.add_argument('url')
    a = p.parse_args()
    print(json.dumps(yearbook2011_catalog(a.keyword) if a.cmd == 'catalog' else yearbook2011_table(a.url), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
