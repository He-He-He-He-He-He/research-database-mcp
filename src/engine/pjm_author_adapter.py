"""Publisher's full author index and author-specific records for PJM."""
import release_runtime
from urllib.parse import urljoin, urlsplit, parse_qs, unquote
import re
import requests
from bs4 import BeautifulSoup
BASE = 'https://msp.org/'
INDEX = BASE + 'index/ai.php'

def _index(session):
    r = session.get(INDEX, params={'jpath': 'pjm'}, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.text, 'html.parser')
    if not s.title or s.title.get_text(' ', strip=True) != 'Pacific Journal of Mathematics - Author Index' or (not s.select('td.letterChunk a.name')):
        raise ValueError('作者索引来源或页面不匹配')
    return s

def authors(query, limit=10, session=None):
    if not isinstance(query, str) or not query.strip() or len(query) > 100 or (type(limit) is not int) or (not 1 <= limit <= 20):
        raise ValueError('需要作者关键词及 1–20 条上限')
    q = query.strip()
    s = _index(session or requests)
    out = []
    for a in s.select('td.letterChunk a.name'):
        name = a.get_text(' ', strip=True)
        href = a.get('href', '')
        u = urlsplit(urljoin(INDEX, href))
        params = parse_qs(u.query)
        if q.casefold() not in name.casefold() or u.hostname != 'msp.org' or u.path != '/index/ail.php' or (params.get('jpath') != ['pjm']) or (not re.fullmatch('[A-Z]', (params.get('l') or [''])[0])) or (not u.fragment):
            continue
        out.append({'name': name})
    return {'source': 'Pacific Journal of Mathematics 出版社作者索引', 'query': q, 'matched': len(out), 'items': out[:limit], 'note': '出版商当前作者索引的姓名子串匹配；不同同名作者可能合并，非全文或浙大订购权限。'}

def author_records(name, limit=10, session=None):
    if not isinstance(name, str) or not name.strip() or len(name) > 150 or (type(limit) is not int) or (not 1 <= limit <= 20):
        raise ValueError('需要完整作者姓名及 1–20 条上限')
    name = name.strip()
    sess = session or requests
    s = _index(sess)
    matches = []
    for a in s.select('td.letterChunk a.name'):
        if a.get_text(' ', strip=True).casefold() == name.casefold():
            matches.append(a)
    if len(matches) != 1:
        raise ValueError('作者不存在或姓名不唯一，请先查询作者索引')
    u = urlsplit(urljoin(INDEX, matches[0].get('href', '')))
    params = parse_qs(u.query)
    if u.hostname != 'msp.org' or u.path != '/index/ail.php' or params.get('jpath') != ['pjm'] or (not re.fullmatch('[A-Z]', (params.get('l') or [''])[0])) or (not u.fragment):
        raise ValueError('作者索引链接不符合预期')
    r = sess.get(BASE + 'index/ail.php', params={'jpath': 'pjm', 'l': params['l'][0]}, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.text, 'html.parser')
    node = s.find(id=unquote(u.fragment))
    if not node or 'authorName' not in (node.get('class') or []):
        raise ValueError('未找到对应作者区块')
    block = node.find_parent('td', class_='authorBlock')
    items = []
    for paper in block.select('div.paper') if block else []:
        t = paper.select_one('.paperTitle')
        ref = paper.select_one('.paperReference')
        a = ref.select_one('a') if ref else None
        if not t or not ref:
            continue
        doi = None
        if a:
            x = urlsplit(a.get('href', ''))
            if x.hostname in ('doi.org', 'dx.doi.org') and x.path.startswith('/10.'):
                doi = 'https://doi.org' + x.path
        items.append({'title': ' '.join(t.get_text(' ', strip=True).split()), 'citation': ' '.join(ref.get_text(' ', strip=True).split()), 'doi': doi})
    if not items:
        raise ValueError('未识别该作者论文题录')
    return {'source': 'Pacific Journal of Mathematics 出版社作者索引', 'author': name, 'indexed_author_name': node.get_text(' ', strip=True), 'total': len(items), 'items': items[:limit], 'note': '作者索引内该姓名对应的单刊题录；同名作者可能混合，不证明全文或浙大机构权限。'}
