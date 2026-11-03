"""ZJU-branded Zhangyue channel public e-book first-page catalog."""
import release_runtime
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
BASE = 'https://se.zhangyue.com/'
APP = 'bf371033'

def search(keyword, limit=50, session=None, page=1):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100:
        raise ValueError('关键词须为 1–100 字')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 50):
        raise ValueError('返回数量须为 1–50')
    if not isinstance(page, int) or isinstance(page, bool) or (not 1 <= page <= 10):
        raise ValueError('页码须为 1–10')
    q = keyword.strip()
    s = session or requests.Session()
    r = s.get(BASE + 'search/index', params={'appId': APP, 'keyword': q}, timeout=20)
    r.raise_for_status()
    p = BeautifulSoup(r.content, 'html.parser')
    if not p.title or p.title.get_text(strip=True) != '浙江大学图书馆' or q not in p.get_text(' ', strip=True):
        raise RuntimeError('频道或搜索词未确认')
    root = p.select_one('ul[data-js="book-autopage"]')
    if root is None:
        if '暂无搜索结果' in p.get_text(' ', strip=True) and page == 1:
            return {'source': '掌阅精选浙江大学图书馆频道', 'query': q, 'page': 1, 'items': [], 'note': '频道名不代表机构身份或全文权限；未提供总书数。'}
        raise RuntimeError('未识别电子书搜索结果')
    total_page = root.get('totalpage', '')
    rel = root.get('rel', '')
    u = urlparse(rel)
    params = parse_qs(u.query)
    if not total_page.isdigit() or root.get('curpage') != '1' or u.scheme != 'https' or (u.hostname != 'se.zhangyue.com') or (u.path != '/search/index') or (params.get('keyword') != [q]) or (params.get('appId') != [APP]) or (params.get('bookType') != ['1']) or (params.get('isAjax') != ['1']) or (params.get('nextRowId') != ['2']):
        raise RuntimeError('原站分页上下文异常')
    if page > int(total_page):
        raise ValueError('请求页超出原站总页数')
    for current in range(2, page + 1):
        params = {'keyword': q, 'bookType': '1', 'nextRowId': str(current), 'isAjax': '1', 'appId': APP, 'currentPage': current}
        r = s.get(BASE + 'search/index', params=params, timeout=20)
        r.raise_for_status()
        try:
            j = r.json()
        except ValueError:
            raise RuntimeError('原站分页未返回 JSON') from None
        d = j.get('data') if isinstance(j, dict) and j.get('code') == 0 else None
        if not isinstance(d, dict) or not isinstance(d.get('html'), str) or d.get('nextRowId') != current + 1:
            raise RuntimeError('原站分页响应异常')
        root = BeautifulSoup(d['html'], 'html.parser')
    items = []
    for a in root.select('a[href]'):
        u = urlparse(a['href'])
        params = parse_qs(u.query)
        b = params.get('bookId', [])
        if u.scheme != 'https' or u.hostname != 'se.zhangyue.com' or u.path != '/book/detail' or (len(b) != 1) or (not b[0].isdigit()) or (params.get('bookType') != ['1']) or (params.get('appId') != [APP]):
            raise RuntimeError('电子书链接异常')
        title = a.select_one('.bookname')
        author = a.select_one('.bk_author')
        publisher = a.select_one('.bk_publisher')
        if not title or not title.get_text(strip=True):
            raise RuntimeError('电子书题名缺失')
        items.append({'id': b[0], 'title': title.get_text('', strip=True), 'author': author.get_text(' ', strip=True) if author else None, 'publisher': publisher.get_text(' ', strip=True) if publisher else None, 'url': a['href']})
    if len(items) > 50:
        raise RuntimeError('首屏结果过多')
    return {'source': '掌阅精选浙江大学图书馆频道', 'query': q, 'page': page, 'total_pages_raw': int(total_page), 'source_page_items': len(items), 'truncated': len(items) > limit, 'items': items[:limit], 'note': '频道名不代表机构身份或全文权限；站方未提供总书数。分页响应未回显页码和关键词，使用首屏同会话及 nextRowId 校验；limit仅截取原站当前页，如truncated为true，翻下一源页会遗漏其余记录，请用limit=50读取本站页。'}
