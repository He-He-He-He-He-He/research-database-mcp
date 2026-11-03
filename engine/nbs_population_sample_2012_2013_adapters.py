"""国家统计局2012、2013年人口变动调查 XLS 样本原表。"""
import release_runtime
import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
SPECS = {2012: (2013, 3, 10, 18, 'html/sm03.htm'), 2013: (2014, 2, 8, 16, 'zk/html/sm02.jpg')}

def get(year, path):
    ed = SPECS[year][0]
    base = f'https://www.stats.gov.cn/sj/ndsj/{ed}/'
    r = requests.get(urljoin(base, path), timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
    r.raise_for_status()
    p = urlparse(r.url)
    if p.scheme != 'https' or p.hostname != 'www.stats.gov.cn' or (not p.path.startswith(f'/sj/ndsj/{ed}/')):
        raise ValueError('非统计局年鉴 HTTPS')
    return r.content

def catalog(year):
    if year not in SPECS:
        raise ValueError('仅支持2012、2013')
    ed, chapter, lo, hi, note = SPECS[year]
    base = f'https://www.stats.gov.cn/sj/ndsj/{ed}/'
    s = BeautifulSoup(get(year, 'left.htm').decode('gb18030'), 'html.parser')
    items = []
    seen = set()
    for a in s.select('a[href]'):
        title = ' '.join(a.get_text(' ', strip=True).split())
        m = re.match('^' + str(chapter) + '-(\\d+)\\s', title)
        path = a['href'].replace('\\', '/')
        if not m or not lo <= int(m.group(1)) <= hi or (not re.fullmatch('(?:zk/)?html/Z0[23]\\d{2}C\\.htm', path, re.I)) or (path.lower() in seen):
            continue
        seen.add(path.lower())
        items.append({'table': int(m.group(1)), 'title': title, 'path': path, 'url': urljoin(base, path)})
    if len(items) != 9:
        raise ValueError('样本表目录结构变化')
    return {'survey_year': year, 'yearbook_edition': ed, 'items': items, 'chapter_note_url': urljoin(base, note), 'scope': '调查样本表，不是全国推算数'}

def detail(year, number):
    item = next((x for x in catalog(year)['items'] if x['table'] == number), None)
    if not item:
        raise ValueError('非该年样本表')
    page = BeautifulSoup(get(year, item['path']).decode('gb18030'), 'html.parser')
    links = []
    for a in page.select('a[href]'):
        href = a['href'].strip()
        if re.fullmatch('[A-Za-z0-9_-]+\\.xls', href, re.I):
            links.append(urljoin(item['url'], href))
    links = list(dict.fromkeys(links))
    if len(links) != 1:
        raise ValueError('未识别唯一 XLS 附件')
    p = urlparse(links[0])
    ed = SPECS[year][0]
    if p.scheme != 'https' or p.hostname != 'www.stats.gov.cn' or (not p.path.startswith(f'/sj/ndsj/{ed}/')):
        raise ValueError('XLS 非年鉴站点')
    try:
        import xlrd
    except ImportError:
        sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
        try:
            import xlrd
        except ImportError as e:
            raise RuntimeError('读取 XLS 需要 xlrd') from e
    b = xlrd.open_workbook(file_contents=get(year, p.path.split(f'/sj/ndsj/{ed}/', 1)[1]), formatting_info=True)
    sheets = []
    for s in b.sheets():
        nonempty = [(r, c) for r in range(s.nrows) for c in range(s.ncols) if s.cell_value(r, c) != '']
        width = max((c for r, c in nonempty), default=-1) + 1
        rows = []
        for n in range(s.nrows):
            cells = s.row_values(n, end_colx=width)
            if any((v != '' for v in cells)):
                rows.append({'row': n + 1, 'values': cells})
        sheets.append({'name': s.name, 'width_nonempty': width, 'merged_cells_zero_based_half_open': [list(x) for x in s.merged_cells], 'rows': rows})
    return {'source': item, 'source_xls_url': links[0], 'chapter_note_url': catalog(year)['chapter_note_url'], 'sheets': sheets, 'note': '原始 XLS 数值可能比表格显示精度更高；空白保留，合并区间为零基右端开。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    l = sub.add_parser('list')
    l.add_argument('year', type=int, choices=sorted(SPECS))
    d = sub.add_parser('detail')
    d.add_argument('year', type=int, choices=sorted(SPECS))
    d.add_argument('table', type=int)
    a = p.parse_args()
    print(json.dumps(catalog(a.year) if a.command == 'list' else detail(a.year, a.table), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
