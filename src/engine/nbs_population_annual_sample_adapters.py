"""国家统计局2006—2009、2011年人口变动调查样本年鉴原表。"""
import release_runtime
import argparse
import json
import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
SPECS = {2006: (2007, 7, 15, 'html/cn04b.htm', 4), 2007: (2008, 7, 15, 'html/j03c.htm', 3), 2008: (2009, 7, 15, 'html/j03.htm', 3), 2009: (2010, 7, 15, 'html/sm03.htm', 3), 2011: (2012, 8, 16, 'html/sm03.htm', 3)}

def get(year, path):
    edition = SPECS[year][0]
    base = f'https://www.stats.gov.cn/sj/ndsj/{edition}/'
    r = requests.get(urljoin(base, path), timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
    r.raise_for_status()
    p = urlparse(r.url)
    if p.scheme != 'https' or p.hostname != 'www.stats.gov.cn' or (not p.path.startswith(f'/sj/ndsj/{edition}/')):
        raise ValueError('非统计局官方 HTTPS 年鉴页面')
    return r.content.decode('utf16' if r.content.startswith((b'\xff\xfe', b'\xfe\xff')) else 'gb18030')

def catalog(year):
    if year not in SPECS:
        raise ValueError('仅支持2006—2009、2011年')
    edition, lo, hi, note, chapter = SPECS[year]
    base = f'https://www.stats.gov.cn/sj/ndsj/{edition}/'
    s = BeautifulSoup(get(year, 'left.htm'), 'html.parser')
    items = []
    seen = set()
    for a in s.select('a[href]'):
        title = ' '.join(a.get_text(' ', strip=True).split())
        m = re.match('^' + str(chapter) + '-(\\d+)\\s', title)
        path = a['href'].replace('\\', '/')
        if not m or not lo <= int(m.group(1)) <= hi or (not re.fullmatch('html/D0' + str(chapter) + '\\d{2}C\\.HTM', path, re.I)) or (path in seen):
            continue
        seen.add(path)
        items.append({'table': int(m.group(1)), 'title': title, 'path': path, 'url': urljoin(base, path)})
    if len(items) != hi - lo + 1:
        raise ValueError('目录样本表数量变化')
    return {'survey_year': year, 'yearbook_edition': edition, 'items': items, 'note_url': urljoin(base, note), 'scope': '仅样本表，非全国推算数'}

def detail(year, number):
    item = next((x for x in catalog(year)['items'] if x['table'] == number), None)
    if not item:
        raise ValueError('非该年样本表')
    s = BeautifulSoup(get(year, item['path']), 'html.parser')
    tables = []
    for t in s.select('table'):
        if t.select('table'):
            continue
        rows = []
        for tr in t.select('tr'):
            cells = [{'text': ' '.join(c.get_text(' ', strip=True).split()), 'rowspan': c.get('rowspan', '1'), 'colspan': c.get('colspan', '1')} for c in tr.find_all(['td', 'th'], recursive=False)]
            if cells:
                rows.append(cells)
        if rows:
            tables.append({'rows': rows})
    if not tables:
        raise ValueError('未发现原表')
    note = BeautifulSoup(get(year, SPECS[year][3]), 'html.parser').get_text('\n', strip=True)
    return {'source': item, 'survey_year': year, 'tables': tables, 'chapter_note': note, 'scope': '抽样调查样本原始表，不是全国总体数量'}

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
