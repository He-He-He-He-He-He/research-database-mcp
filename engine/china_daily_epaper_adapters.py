"""China Daily 英文数字报：按日期列文章和读取正文。"""
import release_runtime
import argparse
import datetime
import json
import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
ROOT = 'https://epaper.chinadaily.com.cn'
ARTICLE = re.compile('^/a/\\d{6}/\\d{2}/WS[0-9a-fA-F]+\\.html$')

def get(url):
    r = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
    r.raise_for_status()
    if urlparse(r.url).hostname != 'epaper.chinadaily.com.cn':
        raise ValueError('页面重定向至其他域名')
    r.encoding = r.apparent_encoding
    return BeautifulSoup(r.text, 'html.parser')

def edition(date, publication='china', keyword=''):
    d = datetime.date.fromisoformat(date)
    if publication not in ('china', 'global'):
        raise ValueError('publication 须为 china 或 global')
    url = f'{ROOT}/{publication}/{d:%Y-%m}/{d:%d}'
    soup = get(url)
    box = soup.select_one('#lft-art')
    if box is None:
        raise ValueError('未发现数字报文章列表，网站结构可能已变化')
    rows, seen = ([], set())
    for a in box.select('a[href]'):
        link = urljoin(url, a['href'])
        p = urlparse(link)
        title = a.get_text(' ', strip=True)
        if p.hostname == 'epaper.chinadaily.com.cn' and ARTICLE.fullmatch(p.path) and p.path.startswith(f'/a/{d:%Y%m}/{d:%d}/') and title and (link not in seen):
            seen.add(link)
            if keyword.casefold() in title.casefold():
                rows.append({'title': title, 'url': link})
    if not seen:
        raise ValueError('未发现当日文章；日期可能无报纸或网页结构变化')
    return {'date': date, 'publication': publication, 'url': url, 'keyword_scope': '仅当日列表标题', 'articles': rows}

def article(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'epaper.chinadaily.com.cn' or (not ARTICLE.fullmatch(p.path)) or p.query or p.fragment:
        raise ValueError('仅接受 China Daily 数字报文章的官方 HTTPS 地址')
    soup = get(url)
    title = soup.select_one('h1')
    body = soup.select_one('#Content')
    if not title or not body:
        raise ValueError('未找到文章标题或正文')
    restricted = bool(body.select_one('a[href^="/private/"]'))
    for n in body.select('a[href^="/private/"], script, style'):
        n.decompose()
    for n in body.select('div'):
        if n.select_one('img[src*="enapp.chinadaily.com.cn"]'):
            n.decompose()
    for n in body.select('script, style'):
        n.decompose()
    media = [{'type': n.name, 'url': urljoin(url, n['src'])} for n in body.select('img[src],video[src],audio[src],source[src]')]
    return {'url': url, 'title': title.get_text(' ', strip=True), 'subscription_link_present': restricted, 'text': body.get_text('\n', strip=True), 'media': media}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    e = sub.add_parser('edition')
    e.add_argument('date')
    e.add_argument('--publication', choices=['china', 'global'], default='china')
    e.add_argument('--keyword', default='')
    a = sub.add_parser('article')
    a.add_argument('url')
    args = parser.parse_args()
    result = edition(args.date, args.publication, args.keyword) if args.command == 'edition' else article(args.url)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
