"""央视网评页面内嵌文章存档和官方文章正文。"""
import release_runtime
import argparse
import json
import re
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
INDEX = 'https://news.cctv.com/yswp/'
ARTICLE = re.compile('^/\\d{4}/\\d{2}/\\d{2}/ARTI[A-Za-z0-9]+\\.shtml$')
HOSTS = {'opinion.cctv.com', 'news.cctv.com'}

def fetch(url):
    r = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
    r.raise_for_status()
    p = urlparse(r.url)
    if p.scheme != 'https' or p.hostname not in HOSTS:
        raise ValueError('非央视网 HTTPS 跳转')
    return r.content.decode('utf-8')

def listing(page=1, page_size=20, keyword=''):
    if page < 1 or not 1 <= page_size <= 100:
        raise ValueError('页码须为正，page_size 须为 1—100')
    html = fetch(INDEX)
    m = re.search('var\\s+obj\\s*=\\s*(\\[.*?\\])\\s*for\\s*\\(', html, re.S)
    if not m:
        raise ValueError('未找到文章数组，页面结构可能已变化')
    records = json.loads(m.group(1))
    rows = [x for x in records if keyword.casefold() in str(x.get('title', '')).casefold()]
    return {'source_url': INDEX, 'total_before_filter': len(records), 'total_after_filter': len(rows), 'page': page, 'page_size': page_size, 'items': rows[(page - 1) * page_size:page * page_size]}

def article(url):
    p = urlparse(url)
    if p.scheme not in ('http', 'https') or p.hostname not in HOSTS or (not ARTICLE.fullmatch(p.path)) or p.query or p.fragment:
        raise ValueError('仅接受央视网官方文章地址')
    url = p._replace(scheme='https').geturl()
    s = BeautifulSoup(fetch(url), 'html.parser')
    h = s.select_one('h1')
    body = s.select_one('#text_area')
    if not h or not body:
        raise ValueError('未找到文章标题或正文')
    for n in body.select('script,style'):
        n.decompose()
    info = s.select_one('.info')
    return {'url': url, 'title': h.get_text(' ', strip=True), 'publication_info': info.get_text(' ', strip=True) if info else None, 'text': body.get_text('\n', strip=True)}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    l = sub.add_parser('list')
    l.add_argument('--page', type=int, default=1)
    l.add_argument('--page-size', type=int, default=20)
    l.add_argument('--keyword', default='')
    a = sub.add_parser('article')
    a.add_argument('url')
    x = p.parse_args()
    print(json.dumps(listing(x.page, x.page_size, x.keyword) if x.command == 'list' else article(x.url), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
