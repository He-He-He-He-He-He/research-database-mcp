"""中国网新闻中心「本网独家」栏目分页列表。"""
import release_runtime
import argparse
import json
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

def page(page=1, keyword='', since='', until=''):
    if not 1 <= page <= 999:
        raise ValueError('page 须在 1 到 999 之间')
    for x in (since, until):
        if x:
            __import__('datetime').date.fromisoformat(x)
    url = 'http://www.china.com.cn/news/node_7065221' + ('' if page == 1 else f'_{page}') + '.htm'
    r = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
    r.raise_for_status()
    if urlparse(r.url).hostname != 'www.china.com.cn' or urlparse(r.url).scheme not in ('http', 'https'):
        raise ValueError('跨域跳转，停止读取')
    r.encoding = r.apparent_encoding
    soup = BeautifulSoup(r.text, 'html.parser')
    entries = soup.select('ul.newsList li')
    if not entries:
        raise ValueError('未找到栏目列表，网站结构可能已变化')
    items = []
    for el in entries:
        a = el.select_one('a[href]')
        t = el.select_one('span')
        if not a:
            continue
        title = a.get_text(' ', strip=True)
        dt = t.get_text(' ', strip=True) if t else ''
        if keyword.casefold() not in title.casefold() or (since and dt < since) or (until and dt > until):
            continue
        items.append({'title': title, 'date_as_displayed': dt or None, 'url': urljoin(url, a['href'])})
    return {'page': page, 'url': url, 'scope': '中国网「本网独家」栏目，筛选仅作用于当前页；原站更新后页码会变化', 'raw_count': len(entries), 'items': items}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--keyword', default='')
    p.add_argument('--since', default='')
    p.add_argument('--until', default='')
    a = p.parse_args()
    print(json.dumps(page(a.page, a.keyword, a.since, a.until), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
