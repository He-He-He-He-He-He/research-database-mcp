"""第一次全国经济普查官方目录与 HTML 原表。"""
import release_runtime
import argparse
import json
import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.stats.gov.cn/sj/pcsj/jjpc/1jp/'
PATH = re.compile('^html/(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_-]+\\.htm$', re.I)

def get(url):
    r = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
    r.raise_for_status()
    p = urlparse(r.url)
    if p.scheme != 'https' or p.hostname != 'www.stats.gov.cn' or (not p.path.startswith('/sj/pcsj/jjpc/1jp/')):
        raise ValueError('非官方资料 HTTPS 跳转')
    return r.content.decode('utf-16' if r.content.startswith((b'\xff\xfe', b'\xfe\xff')) else 'gb18030', errors='strict')

def catalog(keyword=''):
    soup = BeautifulSoup(get(BASE + 'left.htm'), 'html.parser')
    items = []
    seen = set()
    for a in soup.select('a[href]'):
        path = a['href'].replace('\\', '/')
        title = ' '.join(a.get_text(' ', strip=True).split())
        if not PATH.fullmatch(path) or not title or path.lower() in seen:
            continue
        seen.add(path.lower())
        if keyword in title:
            items.append({'title': title, 'path': path, 'url': urljoin(BASE, path)})
    if not seen:
        raise ValueError('目录无可识别条目')
    return {'source_url': BASE + 'left.htm', 'total': len(seen), 'matched_count': len(items), 'count_note': 'total 为全目录数，matched_count 为标题关键词命中数；未命中不代表正文无相关内容。', 'items': items}

def detail(path, keyword=''):
    entries = catalog()['items']
    match = next((x for x in entries if x['path'] == path), None)
    if not match:
        raise ValueError('路径不在官方目录')
    s = BeautifulSoup(get(match['url']), 'html.parser')
    tables = []
    for t in s.select('table'):
        if t.select('table'):
            continue
        rows = []
        for tr in t.select('tr'):
            cells = [{'text': ' '.join(c.get_text(' ', strip=True).split()), 'rowspan': c.get('rowspan', '1'), 'colspan': c.get('colspan', '1')} for c in tr.find_all(['td', 'th'], recursive=False)]
            if cells and (not keyword or keyword in ''.join((x['text'] for x in cells))):
                rows.append(cells)
        if rows:
            tables.append({'rows': rows})
    return {'source': match, 'tables': tables, 'text': s.get_text('\n', strip=True) if not tables and (not keyword) else None, 'filter_scope': '仅原表行文字；筛选可能不包括表头、合并项及注释'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    a = sub.add_parser('list')
    a.add_argument('--keyword', default='')
    d = sub.add_parser('detail')
    d.add_argument('path')
    d.add_argument('--keyword', default='')
    x = p.parse_args()
    print(json.dumps(catalog(x.keyword) if x.command == 'list' else detail(x.path, x.keyword), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
