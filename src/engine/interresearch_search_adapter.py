"""Public Inter-Research publisher search, one page only."""
import release_runtime
import re
from urllib.parse import urljoin, urlsplit, urlunsplit
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.int-res.com'

def search(query, journal=None, limit=24, session=None, *, page=1):
    if not isinstance(query, str) or not query.strip() or len(query) > 100 or (type(limit) is not int) or (not 1 <= limit <= 24) or (type(page) is not int) or (not 1 <= page <= 1000):
        raise ValueError('需要关键词及 1–24 条上限')
    if journal not in (None, 'meps'):
        raise ValueError('目前只支持 meps 单刊本地筛选或全部期刊')
    q = query.strip()
    if session is None:
        session = requests.Session()
        session.trust_env = False
    params = {'tx_solr[q]': q}
    if page > 1:
        params['tx_solr[groupPage][SearchTypes][Articles]'] = page
    r = session.get(BASE + '/searchresult', params=params, timeout=25)
    r.raise_for_status()
    if urlsplit(r.url).hostname != 'www.int-res.com':
        raise ValueError('搜索响应跳转到未知域名')
    s = BeautifulSoup(r.content, 'html.parser')
    text = s.get_text(' ', strip=True)
    m = re.search('Searched for\\s+["“](.*?)["”]\\.\\s*Found\\s+([\\d,]+)\\s+results', text, re.I)
    if not m or m.group(1).casefold() != q.casefold():
        raise ValueError('搜索词或结果数不匹配')
    nav = next((x for x in s.select('.pagination') if any(('Articles' in a.get('href', '') for a in x.select('a[href]')))), None)
    if page > 1 and (not nav or not nav.select_one('li.active') or nav.select_one('li.active').get_text(' ', strip=True) != str(page)):
        raise ValueError('无法确认文章结果页码')
    if nav and nav.select_one('li.active') and (nav.select_one('li.active').get_text(' ', strip=True) != str(page)):
        raise ValueError('站方文章页码不符')
    rows = []
    for e in s.select('li.search-result.results-entry'):
        a = e.select_one('h4 a')
        u = urlsplit(urljoin(BASE, a.get('href', ''))) if a else None
        if not u or u.hostname != 'www.int-res.com' or (not re.match('^/journals/[a-z]+/articles/', u.path)):
            continue
        code = u.path.split('/')[2]
        if journal and code != journal:
            continue
        meta = e.select_one('p.font-bold')
        details = {}
        for d in e.select('.results-teaser div'):
            label = d.find('strong')
            if label and label.get_text(' ', strip=True) in ('Authors:', 'DOI:'):
                key = label.get_text(' ', strip=True)[:-1].lower()
                label.extract()
                details[key] = d.get_text(' ', strip=True)
        rows.append({'title': a.get_text(' ', strip=True), 'journal_code': code, 'citation_raw': meta.get_text(' ', strip=True) if meta else None, 'authors_raw': details.get('authors'), 'doi_raw': details.get('doi'), 'url': urlunsplit((u.scheme, u.netloc, u.path, '', ''))})
    return {'source': 'Inter-Research 官网', 'query': q, 'publisher_total': int(m.group(2).replace(',', '')), 'journal_filter': journal, 'page': page, 'page_matching_count': len(rows), 'page_truncated': len(rows) > limit, 'items': rows[:limit], 'note': '本地截断后下一页不会补回；跨请求排序可能变化。出版社搜索当前文章页，可能包含多个期刊；单刊筛选仅作用于当前页，publisher_total 不是单刊总数。未验证浙大订阅或全文权限。'}
