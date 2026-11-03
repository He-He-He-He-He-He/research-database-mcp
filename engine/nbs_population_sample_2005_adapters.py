"""2005 年 1% 人口抽样调查：中国统计年鉴 2006 样本原表。"""
import release_runtime
import argparse
import json
import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.stats.gov.cn/sj/ndsj/2006/'

def get(path):
    r = requests.get(urljoin(BASE, path), timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
    r.raise_for_status()
    p = urlparse(r.url)
    if p.scheme != 'https' or p.hostname != 'www.stats.gov.cn' or (not p.path.startswith('/sj/ndsj/2006/')):
        raise ValueError('非统计局年鉴 HTTPS 跳转')
    return r.content.decode('utf16' if r.content.startswith((b'\xff\xfe', b'\xfe\xff')) else 'gb18030')

def catalog():
    s = BeautifulSoup(get('left.htm'), 'html.parser')
    items = []
    seen = set()
    for a in s.select('a[href]'):
        title = ' '.join(a.get_text(' ', strip=True).split())
        m = re.match('^4-(\\d+)\\s', title)
        path = a['href'].replace('\\', '/')
        if not m or not 7 <= int(m.group(1)) <= 18 or (not re.fullmatch('html/D04\\d{2}C\\.HTM', path, re.I)) or (path in seen):
            continue
        seen.add(path)
        items.append({'table': int(m.group(1)), 'title': title, 'path': path, 'url': urljoin(BASE, path)})
    if len(items) != 12:
        raise ValueError('样本表目录变化，需重新核验')
    return {'source_url': urljoin(BASE, 'left.htm'), 'items': items, 'note_url': urljoin(BASE, 'html/cn04b.htm'), 'scope': '年鉴 4-7 至 4-18；各表为 1% 调查样本数据'}

def detail(number):
    item = next((x for x in catalog()['items'] if x['table'] == number), None)
    if not item:
        raise ValueError('仅支持样本表 4-7 至 4-18')
    soup = BeautifulSoup(get(item['path']), 'html.parser')
    tables = []
    for t in soup.select('table'):
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
        raise ValueError('未找到表格')
    note = BeautifulSoup(get('html/cn04b.htm'), 'html.parser').get_text('\n', strip=True)
    return {'source': item, 'tables': tables, 'chapter_note': note, 'scope': '样本原始表；不要当全国总体数量'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='command', required=True)
    s.add_parser('list')
    d = s.add_parser('detail')
    d.add_argument('table', type=int, choices=range(7, 19))
    a = p.parse_args()
    print(json.dumps(catalog() if a.command == 'list' else detail(a.table), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
