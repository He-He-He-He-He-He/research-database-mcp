"""《中国人口普查年鉴-2020》官方目录及原表地址。"""
import release_runtime
import argparse
import json
import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.stats.gov.cn/sj/pcsj/rkpc/7rp/zk/'
PATH = re.compile('^html/[A-Za-z0-9_-]+\\.(?:jpg|pdf|htm)$', re.I)

def get(url):
    r = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
    r.raise_for_status()
    p = urlparse(r.url)
    if p.scheme != 'https' or p.hostname != 'www.stats.gov.cn' or (not p.path.startswith('/sj/pcsj/rkpc/7rp/zk/')):
        raise ValueError('非官方 HTTPS 页面')
    return r.content.decode('gb18030', errors='strict')

def catalog(keyword=''):
    s = BeautifulSoup(get(BASE + 'left.htm'), 'html.parser')
    items = []
    seen = set()
    section = None
    for a in s.select('a[href]'):
        path = a['href'].replace('\\', '/')
        title = ' '.join(a.get_text(' ', strip=True).split())
        if '第一部分' in title:
            section = '全部数据资料'
        elif '第二部分' in title:
            section = '长表数据资料'
        elif '第三部分' in title:
            section = '附录'
        if not PATH.fullmatch(path) or not title or path.lower() in seen:
            continue
        seen.add(path.lower())
        if keyword in title:
            items.append({'title': title, 'part': section, 'path': path, 'format': path.rsplit('.', 1)[-1].lower(), 'url': urljoin(BASE, path)})
    if not seen:
        raise ValueError('未找到年鉴目录')
    return {'source_url': BASE + 'left.htm', 'total': len(seen), 'matched_count': len(items), 'count_note': 'total 为全目录数，matched_count 为标题关键词命中数；未命中不代表正文无相关内容。', 'scope': '年鉴目录条目，图片/PDF 不自动提取数值', 'items': items}

def detail(path):
    item = next((x for x in catalog()['items'] if x['path'] == path), None)
    if not item:
        raise ValueError('路径不在官方目录')
    result = dict(item)
    if item['format'] == 'htm':
        result['text'] = BeautifulSoup(get(item['url']), 'html.parser').get_text('\n', strip=True)
    return result

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    l = sub.add_parser('list')
    l.add_argument('--keyword', default='')
    d = sub.add_parser('detail')
    d.add_argument('path')
    a = p.parse_args()
    print(json.dumps(catalog(a.keyword) if a.command == 'list' else detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
