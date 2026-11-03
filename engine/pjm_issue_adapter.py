"""Pacific Journal of Mathematics publisher issue table of contents."""
import release_runtime
import re
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
BASE = 'https://msp.org/pjm/'

def issue(year, volume, number, keyword='', session=None):
    if any((type(x) is not int for x in (year, volume, number))) or not 1950 <= year <= 2100 or (not 1 <= volume <= 9999) or (not 1 <= number <= 4) or (not isinstance(keyword, str)) or (len(keyword) > 100):
        raise ValueError('需要有效年份、卷号、期号及可选关键词')
    url = f'{BASE}{year}/{volume}-{number}/'
    r = (session or requests).get(url, timeout=20)
    r.raise_for_status()
    u = urlsplit(r.url)
    if u.hostname != 'msp.org' or u.path != f'/pjm/{year}/{volume}-{number}/':
        raise ValueError('期刊响应地址不匹配')
    soup = BeautifulSoup(r.text, 'html.parser')
    title = soup.title.get_text(' ', strip=True) if soup.title else ''
    if title != f'Pacific Journal of Mathematics Vol. {volume}, No. {number}, {year}':
        raise ValueError('卷期标题不匹配')
    items = []
    for row in soup.select('td.title-area'):
        a = row.select_one('a.title')
        author = row.select_one('h3')
        pages = row.select_one('.page-numbers')
        if not a or not author:
            continue
        link = urljoin(url, a.get('href', ''))
        u = urlsplit(link)
        if u.hostname != 'msp.org' or not u.path.startswith(f'/pjm/{year}/{volume}-{number}/'):
            continue
        clean = lambda x: ' '.join(x.get_text(' ', strip=True).split())
        items.append({'title': clean(a), 'authors_as_printed': clean(author), 'pages': clean(pages) if pages else None, 'url': link})
    if not items:
        raise ValueError('未找到本期可识别文章')
    matched = [x for x in items if keyword.casefold().strip() in (x['title'] + ' ' + x['authors_as_printed']).casefold()]
    return {'source': 'Pacific Journal of Mathematics (Mathematical Sciences Publishers)', 'year': year, 'volume': volume, 'issue': number, 'issue_url': url, 'issue_items': len(items), 'matched': len(matched), 'items': matched, 'note': '出版社单一卷期公开目录及当前期本地筛选；不表示浙大订购范围或全文权限。'}
