"""EMS Press 网站搜索结果；站方标注 Google Search。"""
import release_runtime
import re
from urllib.parse import urlsplit, parse_qs, urljoin
import requests
from bs4 import BeautifulSoup
BASE = 'https://ems.press'

def search(keyword, page=1, limit=10):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100 or re.search('[\\x00-\\x1f]', keyword):
        raise ValueError('关键词须为 1–100 字单行文本')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 100):
        raise ValueError('页码须为 1–100')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 10):
        raise ValueError('每页最多返回 10 条')
    q = keyword.strip()
    r = requests.get(BASE + '/search', params={'term': q, 'p': page}, timeout=30)
    r.raise_for_status()
    h = BeautifulSoup(r.text, 'html.parser')
    field = h.select_one('form input[name=term]')
    if not h.title or 'Search | EMS Press' not in h.title.get_text(' ', strip=True) or (not field) or (field.get('value') != q) or ('Powered by Google Search' not in h.get_text(' ', strip=True)):
        raise RuntimeError('未确认 EMS Press 搜索页面或关键词')
    rows = h.select('ul.results > li.result-item')
    items = []
    for x in rows:
        a = x.select_one('a[href]')
        title = a.select_one('h2') if a else None
        typ = x.select_one('.resource-type')
        desc = x.select_one('p')
        if not a or not title or (not typ):
            raise RuntimeError('搜索结果缺少标题、类别或链接')
        url = urljoin(BASE, a['href'])
        u = urlsplit(url)
        if u.scheme != 'https' or u.hostname != 'ems.press':
            raise RuntimeError('结果链接不是 EMS Press')
        items.append({'title_snippet': title.get_text(' ', strip=True), 'type_raw': typ.get_text(' ', strip=True), 'url': url, 'snippet': desc.get_text(' ', strip=True) if desc else None})
    nxt = next((a for a in h.select('a[href]') if a.get_text(' ', strip=True) == 'next page'), None)
    if nxt:
        u = urlsplit(urljoin(BASE, nxt['href']))
        p = parse_qs(u.query)
        if u.hostname != 'ems.press' or u.path != '/search' or p.get('term') != [q] or (p.get('p') != [str(page + 1)]):
            raise RuntimeError('下一页链接与查询不一致')
    return {'source': 'EMS Press 网站搜索（Google Search 提供）', 'query': q, 'page_requested': page, 'source_page_items': len(items), 'truncated': len(items) > limit, 'items': items[:limit], 'next_page_available': bool(nxt), 'note': '站方搜索为 Google 索引，结果混合图书与文章，标题及片段可能截断；无总数、未回显本页页码。无结果时页面提示不明确，不能确认确无记录；学校机构和全文权限未验证；limit只截取源站当前页，若truncated为true，翻到下一源页会遗漏余项，请用limit=10取整页。'}
