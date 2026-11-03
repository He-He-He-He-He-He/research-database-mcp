"""Public title metadata from a BJGP search, not institutional full text."""
import release_runtime
import re
from urllib.parse import quote, urljoin, urlsplit, urlunsplit
import requests
from bs4 import BeautifulSoup
BASE = 'https://bjgp.org'

def search(query, limit=10, session=None, *, page=1):
    if not isinstance(query, str) or not query.strip() or len(query) > 100 or (type(limit) is not int) or (not 1 <= limit <= 10) or (type(page) is not int) or (not 1 <= page <= 1000):
        raise ValueError('需要关键词及 1–10 条上限')
    q = query.strip()
    if session is None:
        session = requests.Session()
        session.trust_env = False
    response = session.get(BASE + '/search/' + quote(q, safe=''), params={'page': page - 1} if page > 1 else None, timeout=20)
    response.raise_for_status()
    if urlsplit(response.url).hostname != 'bjgp.org':
        raise ValueError('期刊响应跳转到未知域名')
    soup = BeautifulSoup(response.text, 'html.parser')
    heading = soup.select_one('#page-title')
    text = soup.get_text(' ', strip=True)
    m = re.fullmatch('([\\d,]+)\\s+Results?', heading.get_text(' ', strip=True) if heading else '', re.I)
    if not m or ('for term "' + q + '"').casefold() not in text.casefold():
        raise ValueError('无法确认搜索词或结果数量')
    total = int(m.group(1).replace(',', ''))
    items = []
    active = soup.select_one('.pager-current')
    if active and active.get_text(' ', strip=True) != str(page):
        raise ValueError('站方当前页与请求不符')
    if page > 1 and (not active or (page - 1) * 10 >= total):
        raise ValueError('无法确认页码或页码超出结果范围')
    for row in soup.select('.highwire-search-results-list .highwire-cite'):
        a = row.select_one('a.highwire-cite-linked-title')
        title = row.select_one('.highwire-cite-title')
        if not a or not title:
            continue
        u = urlsplit(urljoin(BASE, a.get('href', '')))
        if u.hostname != 'bjgp.org' or not u.path.startswith('/content/'):
            continue
        get = lambda sel: row.select_one(sel).get_text(' ', strip=True) if row.select_one(sel) else None
        items.append({'title': title.get_text(' ', strip=True), 'authors': [x.get_text(' ', strip=True) for x in row.select('.highwire-citation-author')], 'date_raw': get('.highwire-cite-metadata-date'), 'volume_raw': get('.highwire-cite-metadata-volume'), 'issue_raw': get('.highwire-cite-metadata-issue'), 'pages_raw': get('.highwire-cite-metadata-pages'), 'doi_raw': get('.highwire-cite-metadata-doi'), 'url': urlunsplit((u.scheme, u.netloc, u.path, '', ''))})
    if total and (not items):
        raise ValueError('未能解析本页题录')
    return {'source': 'British Journal of General Practice 官方网站', 'query': q, 'total': total, 'page': page, 'source_page_size': 10, 'source_page_items': len(items), 'page_truncated': len(items) > limit, 'items': items[:limit], 'note': '站方每页10条；本地截断时下一页不会补齐，请取完整10条；跨次查询排序可能变化。公开单期刊全文关键词搜索的当前页题录；不代表全部浙大 ISPG 馆藏或学校订阅、全文权限。医学信息应由专业人员判断。'}
