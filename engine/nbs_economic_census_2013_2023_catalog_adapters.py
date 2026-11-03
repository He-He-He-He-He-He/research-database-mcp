"""国家统计局第三、四、五次经济普查年鉴目录与原表地址。"""
import release_runtime
import argparse
import json
import re
from urllib.parse import urljoin, urlparse, quote
import requests
from bs4 import BeautifulSoup
EDITIONS = {2013: 3, 2018: 4, 2023: 5}
PATH = re.compile('^zk/(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_.-]+ ?\\.(?:jpg|pdf|htm)$', re.I)

def get(year, path):
    base = f'https://www.stats.gov.cn/sj/pcsj/jjpc/{EDITIONS[year]}jp/'
    url = urljoin(base, path)
    r = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
    r.raise_for_status()
    p = urlparse(r.url)
    if p.scheme != 'https' or p.hostname != 'www.stats.gov.cn' or (not p.path.startswith(f'/sj/pcsj/jjpc/{EDITIONS[year]}jp/')):
        raise ValueError('非统计局官方 HTTPS 页面')
    return r.content.decode('gb18030', errors='strict')

def catalog(year, keyword=''):
    if year not in EDITIONS:
        raise ValueError('只支持 2013、2018、2023 年')
    base = f'https://www.stats.gov.cn/sj/pcsj/jjpc/{EDITIONS[year]}jp/'
    s = BeautifulSoup(get(year, 'left.htm'), 'html.parser')
    items = []
    seen = set()
    for a in s.select('a[href]'):
        path = a['href'].replace('\\', '/')
        title = ' '.join(a.get_text(' ', strip=True).split())
        if not PATH.fullmatch(path) or '..' in path or (not title) or (path.lower() in seen):
            continue
        seen.add(path.lower())
        if keyword in title:
            items.append({'title': title, 'path': path, 'format': path.rsplit('.', 1)[-1].lower(), 'url': urljoin(base, quote(path, safe='/'))})
    if not seen:
        raise ValueError('目录无可识别条目')
    return {'year': year, 'source_url': base + 'left.htm', 'total': len(seen), 'matched_count': len(items), 'count_note': 'total 为全目录数，matched_count 为标题关键词命中数；未命中不代表正文无相关内容。', 'scope': '年鉴目录链接；目录不保证原图目前可访问', 'items': items}

def detail(year, path):
    item = next((x for x in catalog(year)['items'] if x['path'] == path), None)
    if not item:
        raise ValueError('路径不在本年鉴目录')
    result = dict(item)
    if item['format'] == 'htm':
        result['text'] = BeautifulSoup(get(year, path), 'html.parser').get_text('\n', strip=True)
    return result

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    l = sub.add_parser('list')
    l.add_argument('year', type=int, choices=sorted(EDITIONS))
    l.add_argument('--keyword', default='')
    d = sub.add_parser('detail')
    d.add_argument('year', type=int, choices=sorted(EDITIONS))
    d.add_argument('path')
    a = p.parse_args()
    print(json.dumps(catalog(a.year, a.keyword) if a.command == 'list' else detail(a.year, a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
