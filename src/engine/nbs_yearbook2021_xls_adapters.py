"""中国统计年鉴 2021 图片目录及同名官方 XLS 资源。"""
import release_runtime
import argparse
from html.parser import HTMLParser
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urljoin, urlsplit
BASE = 'https://www.stats.gov.cn/sj/ndsj/2021/'
INDEX = BASE + 'left.htm'
PATH = re.compile('html/([A-Za-z0-9_-]{1,80})\\.jpg', re.I)

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
        if tag != 'a':
            return
        href = dict(attrs).get('href', '').strip()
        if PATH.fullmatch(href):
            self.active = href
            self.parts = []

    def handle_data(self, text):
        if self.active is not None:
            self.parts.append(text)

    def handle_endtag(self, tag):
        if tag == 'a' and self.active is not None:
            title = ' '.join(''.join(self.parts).split())
            if title:
                self.items[self.active] = {'title': title, 'image_path': self.active, 'image_url': urljoin(BASE, self.active)}
            self.active = None

def yearbook2021_catalog(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 80:
        raise ValueError('关键词须不超过 80 字符')
    p = _Catalog()
    p.feed(_get(INDEX).decode('gb18030'))
    if not p.items:
        raise ValueError('未读取统计年鉴图片目录')
    items = [x for x in p.items.values() if keyword in x['title']]
    return {'source_url': INDEX, 'yearbook': '中国统计年鉴2021', 'total': len(p.items), 'matched_count': len(items), 'items': items, 'note': 'total 为全目录数，matched_count 为标题关键词命中数；目录直接列图片，不承诺每张图都有同名 XLS；表中年份和口径各异。'}

def yearbook2021_table(image_path):
    if not isinstance(image_path, str) or not PATH.fullmatch(image_path):
        raise ValueError('须使用年鉴目录返回的 html/…jpg 路径')
    items = yearbook2021_catalog()['items']
    matched = [x for x in items if x['image_path'] == image_path]
    if len(matched) != 1:
        raise ValueError('图片路径未在当前年鉴目录中')
    try:
        import xlrd
    except ImportError:
        sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
        try:
            import xlrd
        except ImportError as exc:
            raise RuntimeError('XLS 解析需要 xlrd：python3 -m pip install xlrd') from exc
    xls_url = urljoin(BASE, image_path[:-4] + '.xls')
    raw = _get(xls_url)
    if not raw.startswith(bytes.fromhex('d0cf11e0a1b11ae1')):
        raise ValueError('候选文件不是识别的旧版 XLS')
    book = xlrd.open_workbook(file_contents=raw, formatting_info=True)
    sheets = []
    for sh in book.sheets():
        if sh.nrows > 5000 or sh.ncols > 300:
            raise ValueError('表格超出安全尺寸')
        rows = [[{'value': sh.cell_value(r, c), 'cell_type': sh.cell_type(r, c)} for c in range(sh.ncols)] for r in range(sh.nrows)]
        sheets.append({'name': sh.name, 'rows': rows, 'merged_ranges': [{'start_row': a + 1, 'end_row': b, 'start_col': c + 1, 'end_col': d} for a, b, c, d in sh.merged_cells]})
    return {'catalog_entry': matched[0], 'source_xls_url': xls_url, 'yearbook': '中国统计年鉴2021', 'sheets': sheets, 'note': 'XLS 是以图片同名推导并实测存在的候选资源；原始数值可能包含显示格式隐藏的小数，未按显示精度四舍五入；空白不可当零，时间、范围与单位须核对原表。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('catalog')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('table')
    q.add_argument('image_path')
    a = p.parse_args()
    print(json.dumps(yearbook2021_catalog(a.keyword) if a.cmd == 'catalog' else yearbook2021_table(a.image_path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
