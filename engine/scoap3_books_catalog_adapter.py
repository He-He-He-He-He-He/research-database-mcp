"""SCOAP³ Books 项目官网的书单。"""
import release_runtime
from urllib.parse import urlsplit
import requests
from bs4 import BeautifulSoup
URL = 'https://scoap3.org/scoap3-books/'

def search(keyword='', limit=30):
    if not isinstance(keyword, str) or len(keyword) > 100 or any((ord(c) < 32 for c in keyword)):
        raise ValueError('关键词须为不超过 100 字的单行文本')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 200):
        raise ValueError('返回条数须为 1–200')
    r = requests.get(URL, timeout=30)
    r.raise_for_status()
    h = BeautifulSoup(r.text, 'html.parser')
    t = h.select_one('table#tablepress-21')
    if not t:
        raise RuntimeError('未找到 SCOAP³ 官网书单')
    rows = t.select('tr')
    header = [x.get_text(' ', strip=True) for x in rows[0].select('th,td')] if rows else []
    if header != ['Title', 'Author(s)', 'Publisher']:
        raise RuntimeError('官网书单表头变化')
    items = []
    for row in rows[1:]:
        cells = row.select('td')
        if len(cells) != 3:
            raise RuntimeError('官网书单行结构异常')
        title, authors, publisher = [x.get_text(' ', strip=True) for x in cells]
        a = cells[0].select_one('a[href]')
        url = a.get('href') if a else None
        if not title:
            raise RuntimeError('官网书单缺少标题')
        if url and (urlsplit(url).scheme != 'https' or urlsplit(url).hostname not in ('doi.org', 'library.oapen.org')):
            raise RuntimeError('官网书单链接不在已验证域名内')
        items.append({'title': title, 'authors_raw': authors, 'publisher': publisher, 'source_url': url})
    if not items:
        raise RuntimeError('官网书单为空')
    q = keyword.strip().casefold()
    found = [x for x in items if q in ' '.join([x['title'], x['authors_raw'], x['publisher']]).casefold()]
    return {'source': 'SCOAP³ Books 项目官网书单', 'query': keyword.strip(), 'total_catalog': len(items), 'total_matching': len(found), 'limit': limit, 'truncated': len(found) > limit, 'items': found[:limit], 'note': '如 truncated 为 true，可提高 limit（最多200）或缩小关键词；站方书单逐行保留标题、作者及出版社；本地按这三列筛选，不代表搜索图书全文。缺失链接保留空值；项目列为开放获取图书，但逐书实际访问与许可证未验证。'}
