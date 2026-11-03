"""Publisher's public volume contents for the EPH journal in ZJU's single-journal list."""
import release_runtime
from urllib.parse import parse_qs, urljoin, urlsplit, urlunsplit
import requests
from bs4 import BeautifulSoup
BASE = 'https://poj.peeters-leuven.be/content.php'

def _get(session, params):
    r = session.get(BASE, params=params, timeout=20)
    r.raise_for_status()
    if urlsplit(r.url).hostname != 'poj.peeters-leuven.be':
        raise ValueError('期刊响应跳转至未知域名')
    return BeautifulSoup(r.content, 'lxml')

def volumes(session=None):
    if session is None:
        session = requests.Session()
        session.trust_env = False
    soup = _get(session, {'url': 'journal', 'journal_code': 'EPH'})
    found = []
    for a in soup.select('a[href*="url=issue"]'):
        p = parse_qs(urlsplit(a.get('href', '')).query)
        if p.get('journal_code') != ['EPH'] or p.get('issue') != ['0']:
            continue
        v = p.get('vol', [''])[0]
        if v.isdigit() and int(v) not in found:
            found.append(int(v))
    if not found:
        raise ValueError('未识别期刊卷号')
    return {'source': 'Peeters 官方期刊目录', 'journal': 'Études phénoménologiques - Phenomenological Studies', 'volumes': sorted(found), 'note': '仅公开卷号，不代表机构全文权限。'}

def issue(volume, limit=10, session=None):
    if type(volume) is not int or type(limit) is not int or (not 1 <= limit <= 100):
        raise ValueError('需要有效卷号和 1–100 条上限')
    if session is None:
        session = requests.Session()
        session.trust_env = False
    if volume not in volumes(session)['volumes']:
        raise ValueError('卷号不在网站当前目录')
    s = _get(session, {'url': 'issue', 'journal_code': 'EPH', 'issue': '0', 'vol': str(volume)})
    items = []
    for a in s.select('a[href*="url=article"]'):
        p = parse_qs(urlsplit(a.get('href', '')).query)
        if p.get('journal_code') != ['EPH'] or 'download' in p or (not p.get('id', [''])[0].isdigit()):
            continue
        row = a.find_parent('tr')
        cells = row.find_all('td', recursive=False) if row else []
        if len(cells) < 2:
            continue
        parts = [x.strip() for x in cells[1].stripped_strings if x.strip()]
        if not parts:
            continue
        url = urlsplit(urljoin(BASE, a.get('href')))
        if url.hostname != 'poj.peeters-leuven.be':
            continue
        items.append({'id': p['id'][0], 'pages_raw': cells[0].get_text(' ', strip=True), 'title_and_author_raw': parts, 'url': urlunsplit((url.scheme, url.netloc, url.path, url.query, ''))})
    if not items:
        raise ValueError('未识别期刊文章题录')
    return {'source': 'Peeters 官方卷期目录', 'journal': 'Études phénoménologiques - Phenomenological Studies', 'volume': volume, 'matched_count': len(items), 'limit': limit, 'truncated': len(items) > limit, 'items': items[:limit], 'note': '如 truncated 为 true，请提高 limit（最多100）；单卷公开题录；题名、副标题与作者按原始顺序保留，不证明学校订阅或全文权限。'}
