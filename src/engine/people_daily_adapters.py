"""人民网人民日报数字报：按日期和版面浏览，以及读取文章正文。"""
import release_runtime
import argparse
import datetime
import json
import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
ROOT = 'https://paper.people.com.cn'
ARTICLE = re.compile('^/rmrb/(?:pc/content/\\d{6}/\\d{2}/content_\\d+\\.html|html/\\d{4}-\\d{2}/\\d{2}/nw\\.D110000renmrb_\\d{8}_\\d+-\\d+\\.htm)$')
EDITION = re.compile('^/rmrb/(?:pc/layout/\\d{6}/\\d{2}/node_\\d+\\.html|html/\\d{4}-\\d{2}/\\d{2}/nbs\\.D110000renmrb_\\d+\\.htm)$')

def get_soup(url):
    response = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
    response.raise_for_status()
    if urlparse(response.url).hostname != 'paper.people.com.cn':
        raise ValueError('页面重定向至其他域名，停止读取')
    response.encoding = response.apparent_encoding
    return BeautifulSoup(response.text, 'html.parser')

def edition(date, page=1, layout='modern', keyword=''):
    d = datetime.date.fromisoformat(date)
    if not 1 <= page <= 99:
        raise ValueError('版面编号需介于 1 和 99')
    if layout == 'modern':
        path = f'/rmrb/pc/layout/{d:%Y%m}/{d:%d}/node_{page:02}.html'
    elif layout == 'old':
        path = f'/rmrb/html/{d:%Y-%m}/{d:%d}/nbs.D110000renmrb_{page:02}.htm'
    else:
        raise ValueError('layout 必须为 modern 或 old')
    url = ROOT + path
    soup = get_soup(url)
    articles, editions, seen = ([], [], set())
    for a in soup.select('a[href]'):
        link = urljoin(url, a['href'])
        parsed = urlparse(link)
        if parsed.hostname != 'paper.people.com.cn':
            continue
        title = a.get_text(' ', strip=True)
        if not title or link in seen:
            continue
        if ARTICLE.fullmatch(parsed.path):
            seen.add(link)
            if keyword in title:
                articles.append({'title': title, 'url': link})
        elif EDITION.fullmatch(parsed.path):
            seen.add(link)
            editions.append({'title': title, 'url': link})
    if not articles and (not editions) and (not keyword):
        raise ValueError('页面未发现可识别的版面或文章；网站结构可能已变化')
    return {'date': d.isoformat(), 'page': page, 'layout': layout, 'url': url, 'keyword_scope': '仅当前版面标题', 'editions': editions, 'articles': articles}

def article(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'paper.people.com.cn' or (not ARTICLE.fullmatch(p.path)) or p.query or p.fragment:
        raise ValueError('仅接受人民日报数字报文章的官方 HTTPS 地址')
    soup = get_soup(url)
    title, body = (soup.select_one('h1'), soup.select_one('#ozoom'))
    if not title or not body:
        raise ValueError('未找到文章标题或正文；网站结构可能已变化')
    for node in body.select('script,style'):
        node.decompose()
    media = []
    for node in body.select('img[src],video[src],audio[src],source[src]'):
        src = urljoin(url, node['src'])
        caption = BeautifulSoup(node.get('data-original-title', ''), 'html.parser').get_text(' ', strip=True)
        media.append({'type': node.name, 'url': src, 'caption': caption})
    return {'url': url, 'title': title.get_text(' ', strip=True), 'text': body.get_text('\n', strip=True), 'media': media}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    e = sub.add_parser('edition')
    e.add_argument('date')
    e.add_argument('--page', type=int, default=1)
    e.add_argument('--layout', choices=['modern', 'old'], default='modern')
    e.add_argument('--keyword', default='')
    a = sub.add_parser('article')
    a.add_argument('url')
    args = parser.parse_args()
    result = edition(args.date, args.page, args.layout, args.keyword) if args.command == 'edition' else article(args.url)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
