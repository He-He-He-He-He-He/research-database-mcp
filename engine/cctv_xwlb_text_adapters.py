"""央视网新闻联播逐日节目索引和网页配套文字。"""
import release_runtime
import argparse
import datetime
import json
import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
PATTERN = re.compile('^/\\d{4}/\\d{2}/\\d{2}/VIDE[A-Za-z0-9]+\\.shtml$')

def get(url):
    r = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
    r.raise_for_status()
    p = urlparse(r.url)
    if p.scheme != 'https' or p.hostname != 'tv.cctv.com':
        raise ValueError('页面跳出央视网 HTTPS')
    r.encoding = r.apparent_encoding
    return BeautifulSoup(r.text, 'html.parser')

def day(date, keyword=''):
    d = datetime.date.fromisoformat(date)
    url = f'https://tv.cctv.com/lm/xwlb/day/{d:%Y%m%d}.shtml'
    s = get(url)
    items = []
    seen = set()
    for a in s.select('li a[href]'):
        title = a.get_text(' ', strip=True)
        link = urljoin(url, a['href'])
        p = urlparse(link)
        if p.hostname != 'tv.cctv.com' or not PATTERN.fullmatch(p.path) or (not title) or (p.path in seen):
            continue
        seen.add(p.path)
        if keyword.casefold() in title.casefold():
            items.append({'title': title, 'url': p._replace(scheme='https').geturl()})
    if not seen:
        raise ValueError('未识别节目条目，日期可能不可用或网页结构变化')
    return {'date': date, 'source_url': url, 'total_before_filter': len(seen), 'keyword_scope': '仅当日标题', 'items': items}

def article(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'tv.cctv.com' or (not PATTERN.fullmatch(p.path)) or p.query or p.fragment:
        raise ValueError('仅接受央视节目视频页面的 HTTPS 地址')
    s = get(url)
    body = s.select_one('.content_area') or s.select_one('.cnt_bd')
    if body is None:
        raise ValueError('页面未找到配套文字区')
    for n in body.select('script,style'):
        n.decompose()
    text = body.get_text('\n', strip=True)
    return {'url': url, 'text_available': bool(text), 'text': text, 'scope': '网页配套文字；不保证逐字稿或全期内容'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    d = sub.add_parser('day')
    d.add_argument('date')
    d.add_argument('--keyword', default='')
    a = sub.add_parser('article')
    a.add_argument('url')
    v = p.parse_args()
    print(json.dumps(day(v.date, v.keyword) if v.command == 'day' else article(v.url), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
