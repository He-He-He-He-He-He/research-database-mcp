"""China Disabled Persons Federation statistical yearbook thematic HTML tables."""
import release_runtime
import re
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
INDEX = 'https://www.cdpf.org.cn/ndsj11/index.htm'
PREFIX = '/zwgk/zccx/ndsj/'

def _allowed(url):
    p = urlsplit(url)
    return p.scheme == 'https' and p.netloc == 'www.cdpf.org.cn' and (not p.query) and (not p.fragment) and (p.path == '/ndsj11/index.htm' or re.fullmatch('/zwgk/zccx/ndsj/[A-Za-z0-9_/-]+/[a-f0-9]+\\.htm', p.path))

def _get(url):
    if not _allowed(url):
        raise ValueError('only official yearbook pages allowed')
    with requests.get(url, timeout=(10, 35), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        b = bytearray()
        for c in r.iter_content(65536):
            b.extend(c)
            if len(b) > 5000000:
                raise ValueError('page too large')
        return bytes(b)

def yearbooks():
    soup = BeautifulSoup(_get(INDEX), 'html.parser')
    out = []
    for a in soup.select('a[href]'):
        title = ' '.join(a.get_text(' ', strip=True).split())
        m = re.fullmatch('(2019|2020|2021)年中国残疾人事业统计年鉴', title)
        u = urljoin(INDEX, a['href'])
        if m and _allowed(u):
            out.append({'yearbook_year': int(m.group(1)), 'title': title, 'url': u})
    if not out:
        raise ValueError('yearbook catalog missing')
    return out

def catalog(yearbook_year, keyword=''):
    if type(yearbook_year) is not int or yearbook_year not in range(2019, 2022):
        raise ValueError('yearbook year 2019–2021')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    roots = [x for x in yearbooks() if x['yearbook_year'] == yearbook_year]
    if len(roots) != 1:
        raise ValueError('yearbook root unavailable')
    u = roots[0]['url']
    soup = BeautifulSoup(_get(u), 'html.parser')
    items = []
    seen = set()
    for a in soup.select('a[href]'):
        title = ' '.join(a.get_text(' ', strip=True).split())
        target = urljoin(u, a['href'])
        if not re.match('^[34]-\\d', title) or not _allowed(target) or target in seen:
            continue
        seen.add(target)
        if keyword in title:
            items.append({'title': title, 'url': target})
    if not seen:
        raise ValueError('thematic navigation missing')
    return {'source': '中国残疾人联合会', 'yearbook_year': yearbook_year, 'source_url': u, 'total': len(seen), 'items': items}

def table(yearbook_year, url):
    entries = [i for i in catalog(yearbook_year)['items'] if i['url'] == url]
    if len(entries) != 1:
        raise ValueError('URL not in selected official yearbook navigation')
    soup = BeautifulSoup(_get(url), 'html.parser')
    tables = []
    for t in soup.select('table'):
        rows = []
        for tr in t.find_all('tr'):
            if tr.find_parent('table') is not t:
                continue
            rows.append([{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)])
        if len(rows) >= 3:
            tables.append(rows)
    if not tables:
        raise ValueError('no HTML table found')
    return {'source': '中国残疾人联合会', 'yearbook_year': yearbook_year, 'title': entries[0]['title'], 'url': url, 'tables': tables, 'note': '原始表格单元格和合并属性；年鉴年不等于各指标数据年，须查原表及说明。空白不当作零。'}
