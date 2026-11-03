"""第二次全国农业普查四卷官方目录及 XLS 原表。"""
import release_runtime
import argparse
import sys
from pathlib import Path
import json
import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
VOLUMES = {'zh': '综合卷', 'ny': '农业卷', 'nc': '农村卷', 'nm': '农民卷'}
PATH = re.compile('^(?:excel|html)/[A-Za-z0-9_.-]+\\.(?:xls|htm|jpg)$', re.I)

def get(volume, path):
    base = f'https://www.stats.gov.cn/sj/pcsj/nypc/nypc2/{volume}/'
    u = urljoin(base, path)
    r = requests.get(u, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
    r.raise_for_status()
    p = urlparse(r.url)
    if p.scheme != 'https' or p.hostname != 'www.stats.gov.cn' or (not p.path.startswith(f'/sj/pcsj/nypc/nypc2/{volume}/')):
        raise ValueError('非官方 HTTPS 跳转')
    return r.content

def catalog(volume, keyword=''):
    if volume not in VOLUMES:
        raise ValueError('无效卷名')
    base = f'https://www.stats.gov.cn/sj/pcsj/nypc/nypc2/{volume}/'
    s = BeautifulSoup(get(volume, 'lefte.htm').decode('gb18030'), 'html.parser')
    items = []
    seen = set()
    for a in s.select('a[href]'):
        path = a['href'].replace('\\', '/')
        title = ' '.join(a.get_text(' ', strip=True).split())
        if not PATH.fullmatch(path) or '..' in path or (not title) or (path.lower() in seen):
            continue
        seen.add(path.lower())
        if keyword in title:
            items.append({'title': title, 'path': path, 'format': path.rsplit('.', 1)[-1].lower(), 'url': urljoin(base, path)})
    if not seen:
        raise ValueError('目录无可识别项目')
    return {'volume': VOLUMES[volume], 'source_url': base + 'lefte.htm', 'total': len(seen), 'matched_count': len(items), 'count_note': 'total 为全目录数，matched_count 为标题关键词命中数；未命中不代表正文无相关内容。', 'items': items}

def detail(volume, path, keyword=''):
    item = next((x for x in catalog(volume)['items'] if x['path'] == path), None)
    if not item:
        raise ValueError('路径不在对应卷的官方目录')
    raw = get(volume, path)
    if item['format'] == 'htm':
        return {'source': item, 'text': BeautifulSoup(raw.decode('gb18030'), 'html.parser').get_text('\n', strip=True)}
    if item['format'] != 'xls':
        return {'source': item, 'note': '该项为图片，不做 OCR'}
    try:
        import xlrd
    except ImportError:
        sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
        try:
            import xlrd
        except ImportError as e:
            raise RuntimeError('读取 XLS 需要安装 xlrd') from e
    b = xlrd.open_workbook(file_contents=raw, formatting_info=True)
    sheets = []
    for s in b.sheets():
        nonempty = [(r, c) for r in range(s.nrows) for c in range(s.ncols) if s.cell_value(r, c) != '']
        width = max((c for r, c in nonempty), default=-1) + 1
        rows = []
        for n in range(s.nrows):
            cells = s.row_values(n, end_colx=width)
            if not any((v != '' for v in cells)):
                continue
            if keyword and (not any((keyword in str(v).replace(' ', '') for v in cells))):
                continue
            rows.append({'row': n + 1, 'values': cells})
        sheets.append({'name': s.name, 'width_nonempty': width, 'merged_cells_zero_based_half_open': [list(x) for x in s.merged_cells], 'rows': rows})
    return {'source': item, 'sheets': sheets, 'note': '单元格值按原 XLS 返回；合并范围为零基、右端开区间；筛选可能不含表头。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    l = sub.add_parser('list')
    l.add_argument('volume', choices=VOLUMES)
    l.add_argument('--keyword', default='')
    d = sub.add_parser('detail')
    d.add_argument('volume', choices=VOLUMES)
    d.add_argument('path')
    d.add_argument('--keyword', default='')
    a = p.parse_args()
    print(json.dumps(catalog(a.volume, a.keyword) if a.command == 'list' else detail(a.volume, a.path, a.keyword), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
