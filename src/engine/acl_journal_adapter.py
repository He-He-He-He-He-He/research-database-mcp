"""Annals of Clinical & Laboratory Science: one publicly visible search page."""
import release_runtime
import re
from urllib.parse import urljoin, urlsplit, urlunsplit
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.annclinlabsci.org'

def search(query, limit=10, session=None, *, page=1):
    if not isinstance(query, str) or not query.strip() or len(query) > 150 or (type(limit) is not int) or (not 1 <= limit <= 10) or (type(page) is not int) or (not 1 <= page <= 1000):
        raise ValueError('需要关键词及 1–10 条上限')
    query = query.strip()
    if session is None:
        session = requests.Session()
        session.trust_env = False
    params = {'fulltext': query, 'submit': 'yes'}
    if page > 1:
        params['FIRSTINDEX'] = (page - 1) * 10
    r = session.get(BASE + '/search', params=params, timeout=20)
    r.raise_for_status()
    if urlsplit(r.url).hostname != 'www.annclinlabsci.org':
        raise ValueError('期刊响应跳转到未知域名')
    soup = BeautifulSoup(r.text, 'html.parser')
    text = soup.get_text(' ', strip=True)
    m = re.search('Displaying results\\s+(\\d+)\\s*[-–]\\s*(\\d+)\\s+of\\s+([\\d,]+)', text, re.I)
    if not m or ('Searching journal content for ' + query + ' in full text').casefold() not in text.casefold():
        raise ValueError('无法确认期刊搜索结果或结果为空；请检查站点响应')
    total = int(m.group(3).replace(',', ''))
    items = []
    if int(m.group(1)) != (page - 1) * 10 + 1 or int(m.group(2)) < int(m.group(1)) or int(m.group(2)) > total:
        raise ValueError('来源结果范围与请求页不符')
    for row in soup.select('div.results-cit.cit'):
        title = row.select_one('.cit-title')
        a = row.select_one('a[rel="abstract"]')
        cite = row.select_one('cite')
        if not title or not a:
            continue
        clean = lambda n: re.sub('\\s+', ' ', ''.join(n.strings)).strip()
        u = urlsplit(urljoin(BASE, a.get('href', '')))
        if u.hostname != 'www.annclinlabsci.org' or not u.path.startswith('/content/'):
            continue
        items.append({'title': clean(title), 'authors': [clean(x) for x in row.select('.cit-auth-type-author')], 'citation': clean(cite) if cite else None, 'url': urlunsplit((u.scheme, u.netloc, u.path, '', ''))})
    if total and (not items):
        raise ValueError('未能解析当前页题录')
    return {'source': 'Annals of Clinical & Laboratory Science', 'query': query, 'total': total, 'page': page, 'source_page_size': 10, 'source_page_items': len(items), 'page_truncated': len(items) > limit, 'items': items[:limit], 'note': '来源每页10条，本地截断时下一页不会补回，请取完整10条；跨请求排序可能变化。原站公开单期刊全文关键词检索当前页题录；不是全部 ISPG 馆藏，不证明浙大机构权限或全文可用。该站网络可能不稳定。'}
