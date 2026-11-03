"""中国新闻网滚动新闻：按日列新闻，按官方链接读取正文。"""
import release_runtime
import argparse
import datetime
import json
import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
ROOT = 'https://www.chinanews.com.cn'
ARTICLE = re.compile('^/[a-z]+/\\d{4}/\\d{2}-\\d{2}/\\d+\\.shtml$')

def get(url):
    r = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
    r.raise_for_status()
    if urlparse(r.url).hostname != 'www.chinanews.com.cn':
        raise ValueError('页面重定向至其他域名，停止读取')
    r.encoding = r.apparent_encoding
    return BeautifulSoup(r.text, 'html.parser')

def day(date, keyword='', category=''):
    d = datetime.date.fromisoformat(date)
    url = f'{ROOT}/scroll-news/{d:%Y}/{d:%m%d}/news.shtml'
    soup = get(url)
    rows = []
    found = soup.select('li:has(.dd_bt)')
    if not found:
        raise ValueError('未找到当天滚动列表，可能无发布或网页结构不同')
    for row in found:
        a = row.select_one('.dd_bt a[href]')
        c = row.select_one('.dd_lm')
        t = row.select_one('.dd_time')
        if not a:
            continue
        title = a.get_text(' ', strip=True)
        label = c.get_text(' ', strip=True).strip('[]【】') if c else ''
        url2 = urljoin(url, a['href'])
        if keyword.casefold() in title.casefold() and category in label:
            rows.append({'title': title, 'category': label, 'time_as_displayed': t.get_text(' ', strip=True) if t else None, 'url': url2})
    return {'date': date, 'url': url, 'scope': '网站当日滚动列表；关键词仅筛选标题', 'list_rows_before_filter': len(found), 'items': rows}

def article(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.chinanews.com.cn' or (not ARTICLE.fullmatch(p.path)) or p.query or p.fragment:
        raise ValueError('仅支持中新网常规文字新闻的官方 HTTPS 地址；视频或外站链接请打开原网页')
    soup = get(url)
    title = soup.select_one('h1')
    body = soup.select_one('.content_maincontent_content') or soup.select_one('.left_zw')
    if not title or not body:
        raise ValueError('未找到标准新闻标题或正文')
    for n in body.select('script, style'):
        n.decompose()
    media = [{'type': n.name, 'url': urljoin(url, n['src'])} for n in body.select('img[src],video[src],audio[src],source[src]')]
    t = soup.select_one('#pubtime_baidu')
    source = soup.select_one('#source_baidu')
    return {'url': url, 'title': title.get_text(' ', strip=True), 'published_at': t.get_text(' ', strip=True) if t else None, 'source_as_displayed': source.get_text(' ', strip=True) if source else None, 'text': body.get_text('\n', strip=True), 'media': media}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    d = sub.add_parser('day')
    d.add_argument('date')
    d.add_argument('--keyword', default='')
    d.add_argument('--category', default='')
    a = sub.add_parser('article')
    a.add_argument('url')
    args = parser.parse_args()
    result = day(args.date, args.keyword, args.category) if args.command == 'day' else article(args.url)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
