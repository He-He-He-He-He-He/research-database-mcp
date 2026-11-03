"""One public search page for Journal of Nuclear Medicine Technology."""
import release_runtime
import re
from urllib.parse import quote, urljoin, urlsplit, urlunsplit
import requests
from bs4 import BeautifulSoup
BASE = 'https://tech.snmjournals.org'

def search(query, limit=5, session=None):
    if not isinstance(query, str) or not query.strip() or len(query) > 100 or ('/' in query) or (type(limit) is not int) or (not 1 <= limit <= 10):
        raise ValueError('需要有效关键词和 1–10 条上限')
    query = query.strip()
    r = (session or requests).get(BASE + '/search/' + quote(query, safe=''), timeout=20)
    r.raise_for_status()
    if urlsplit(r.url).hostname != 'tech.snmjournals.org':
        raise ValueError('来源域名不匹配')
    soup = BeautifulSoup(r.text, 'html.parser')
    text = re.sub('\\s+', ' ', soup.get_text(' ', strip=True))
    m = re.search('([\\d,]+|No)\\s+Results?\\s+for\\s+term\\s+["“]([^"”]+)["”]', text, re.I)
    if not m or m.group(2).casefold() != query.casefold():
        raise ValueError('搜索词或总数未确认')
    total = 0 if m.group(1).casefold() == 'no' else int(m.group(1).replace(',', ''))
    items = []
    for row in soup.select('div.highwire-cite'):
        title = row.select_one('a.highwire-cite-linked-title')
        journal = row.select_one('.highwire-cite-metadata-journal')
        if not title or not journal or journal.get_text(' ', strip=True) != 'Journal of Nuclear Medicine Technology':
            continue
        u = urlsplit(urljoin(BASE, title.get('href', '')))
        if u.hostname != 'tech.snmjournals.org' or not u.path.startswith('/content/'):
            continue
        doi = row.select_one('.highwire-cite-metadata-doi')
        date = row.select_one('.highwire-cite-metadata-date')
        items.append({'title': re.sub('\\s+', ' ', title.get_text('', strip=False).strip()), 'authors': [x.get_text(' ', strip=True) for x in row.select('.highwire-citation-author')], 'date': date.get_text(' ', strip=True).rstrip(',') if date else None, 'doi': doi.get_text(' ', strip=True).removeprefix('DOI: ').strip() if doi else None, 'url': urlunsplit((u.scheme, u.netloc, u.path, '', ''))})
    if total and (not items):
        raise ValueError('当前页未能识别该刊题录')
    return {'source': 'Journal of Nuclear Medicine Technology (SNMMI)', 'query': query, 'total': total, 'items': items[:limit], 'note': '原站公开单刊首屏题录；学校机构、全文权限未验证，不代表全部 ISPG 馆藏；非医疗建议。'}
