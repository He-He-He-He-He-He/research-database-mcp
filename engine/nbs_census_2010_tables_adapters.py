"""国家统计局 2010 第六次人口普查资料目录和 HTML 原表。"""
import release_runtime
import argparse
from html.parser import HTMLParser
import json
import re
import subprocess
from urllib.parse import urljoin, urlsplit
from moe_education_statistics_adapters import _LeafTables
BASE = 'https://www.stats.gov.cn/sj/pcsj/rkpc/6rp/'
INDEX = BASE + 'left.htm'
PATH = re.compile('/sj/pcsj/rkpc/6rp/html/[A-Za-z0-9_]{1,80}\\.[hH][tT][mM]')

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

def census2010_catalog(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 80:
        raise ValueError('关键词须不超过 80 字符')
    p = _Catalog()
    p.feed(_get(INDEX))
    if not p.items:
        raise ValueError('未读取人口普查目录')
    items = [x for x in p.items.values() if keyword in x['title']]
    return {'source_url': INDEX, 'reference_time': '2010-11-01 00:00', 'total': len(p.items), 'matched_count': len(items), 'items': items, 'note': 'total 为全目录数，matched_count 为标题关键词命中数；目录包括短表、长表和附录，未命中标题不代表正文无相关内容，全数调查与抽样长表不能混用。'}

def census2010_table(url):
    u = urlsplit(url)
    if u.scheme != 'https' or u.netloc != 'www.stats.gov.cn' or u.query or u.fragment or (not PATH.fullmatch(u.path)):
        raise ValueError('仅接受第六次人口普查资料的官方 HTML 表地址')
    p = _LeafTables()
    p.feed(_get(url))
    if not p.tables:
        raise ValueError('页面未识别出 HTML 表；可能为说明而非数据表')
    return {'source_url': url, 'reference_time': '2010-11-01 00:00', 'tables': p.tables, 'note': '原始表保留标题、单位、表头、分组和合并属性；有些单元格为空，不能补零；短表和长表、地区、城乡、年龄与调查范围需核对原文。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('catalog')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('table')
    q.add_argument('url')
    a = p.parse_args()
    print(json.dumps(census2010_catalog(a.keyword) if a.cmd == 'catalog' else census2010_table(a.url), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
