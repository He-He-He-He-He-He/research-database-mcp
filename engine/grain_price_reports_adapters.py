"""国家发改委公开的粮食市场监测目录及原表链接。"""
import release_runtime
import argparse
import json
import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.ndrc.gov.cn/fgsj/tjsj/lslt/shichangjiance/'
PATH = re.compile('^/fgsj/tjsj/lslt/shichangjiance/\\d{6}/t\\d{8}_\\d+\\.html$')

def fetch(url):
    r = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
    r.raise_for_status()
    p = urlparse(r.url)
    if p.scheme != 'https' or p.hostname != 'www.ndrc.gov.cn':
        raise ValueError('跨域或非 HTTPS 跳转')
    r.encoding = r.apparent_encoding
    return BeautifulSoup(r.text, 'html.parser')

def listing(keyword=''):
    url = BASE + 'wap_index.html'
    s = fetch(url)
    rows = []
    seen = set()
    for li in s.select('li'):
        a = li.select_one('a[href]')
        if not a:
            continue
        link = urljoin(url, a['href'])
        p = urlparse(link)
        title = a.get_text(' ', strip=True)
        time = li.select_one('span')
        if p.hostname != 'www.ndrc.gov.cn' or not PATH.fullmatch(p.path) or (not title) or (link in seen):
            continue
        seen.add(link)
        if keyword in title:
            rows.append({'title': title, 'published_as_displayed': time.get_text(' ', strip=True) if time else None, 'url': link})
    if not seen:
        raise ValueError('未找到市场监测列表')
    return {'source_url': url, 'total_before_filter': len(seen), 'scope': '发改委现有市场监测列表，关键词筛选标题', 'items': rows}

def detail(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.ndrc.gov.cn' or (not PATH.fullmatch(p.path)) or p.query or p.fragment:
        raise ValueError('仅接受发改委该栏目 HTTPS 正文地址')
    s = fetch(url)
    body = s.select_one('.TRS_Editor')
    title = s.select_one('h1')
    meta = s.select_one('.shezhi')
    if not body:
        raise ValueError('未找到报告正文')
    images = [urljoin(url, i['src']) for i in body.select('img[src]')]
    return {'url': url, 'title': title.get_text(' ', strip=True) if title else None, 'publication_info': meta.get_text(' ', strip=True) if meta else None, 'text': body.get_text('\n', strip=True), 'images': images, 'note': '图像表格未自动识别，数值和监测日期需看原图'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    l = sub.add_parser('list')
    l.add_argument('--keyword', default='')
    d = sub.add_parser('detail')
    d.add_argument('url')
    a = p.parse_args()
    print(json.dumps(listing(a.keyword) if a.command == 'list' else detail(a.url), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
