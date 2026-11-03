"""Official historical China Statistical Yearbook HTML tables (selected years)."""
import release_runtime
import re
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
ROOTS = {1999: 'https://www.stats.gov.cn/yearbook/ml/1999_c.htm', 2000: 'https://www.stats.gov.cn/sj/ndsj/zgnj/mulu.html', 2001: 'https://www.stats.gov.cn/sj/ndsj/2001c/mulu.htm', 2002: 'https://www.stats.gov.cn/yearbook2001/ml/2002_c.htm', 2004: 'https://www.stats.gov.cn/sj/ndsj/yb2004-c/left.htm'}
PREFIX = {1999: '/yearbook/1999/', 2000: '/sj/ndsj/zgnj/2000/', 2001: '/sj/ndsj/2001c/', 2002: '/yearbook2001/2002/', 2004: '/sj/ndsj/yb2004-c/html/'}

def _allowed(url):
    u = urlsplit(url)
    return u.scheme == 'https' and u.netloc == 'www.stats.gov.cn' and (not u.query) and (not u.fragment) and re.fullmatch('/[A-Za-z0-9_./-]+\\.html?', u.path, re.I) and ('..' not in u.path)

def _get(url):
    if not _allowed(url):
        raise ValueError('unexpected source URL')
    with requests.get(url, timeout=(10, 35), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        data = bytearray()
        for c in r.iter_content(65536):
            data.extend(c)
            if len(data) > 5000000:
                raise ValueError('document too large')
        return bytes(data).decode('gb18030', errors='strict')

def catalog(year, keyword=''):
    if type(year) is not int or year not in ROOTS:
        raise ValueError('supported years: 1999, 2000, 2001, 2002, 2004')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    root = ROOTS[year]
    first = BeautifulSoup(_get(root), 'html.parser')
    pages = [(root, first)]
    if year in (2000, 2001):
        chapters = []
        for a in first.select('a[href]'):
            u = urljoin(root, a['href'])
            p = urlsplit(u)
            pattern = '/sj/ndsj/zgnj/mulu[a-z]\\.html' if year == 2000 else '/sj/ndsj/2001c/mulu_[a-z]\\.htm'
            if _allowed(u) and re.fullmatch(pattern, p.path, re.I) and (u not in chapters):
                chapters.append(u)
        if not chapters:
            raise ValueError('chapter index missing')
        pages = [(u, BeautifulSoup(_get(u), 'html.parser')) for u in chapters]
    found = []
    seen = set()
    for base, soup in pages:
        for a in soup.select('a[href]'):
            title = ' '.join(a.get_text(' ', strip=True).split())
            url = urljoin(base, a['href'])
            p = urlsplit(url)
            if not re.match('^(?:\\d+-\\d+|[A-Z]\\d{2})', title, re.I):
                continue
            if not _allowed(url) or not p.path.startswith(PREFIX[year]) or url in seen:
                continue
            seen.add(url)
            if keyword in title:
                found.append({'title': title, 'url': url})
    if not seen:
        raise ValueError('no historical tables found')
    return {'source': '国家统计局中国统计年鉴', 'yearbook_year': year, 'catalog_url': root, 'total': len(seen), 'matched_count': len(found), 'count_note': 'total 为全目录数，matched_count 为标题关键词命中数；未命中不代表表格内容无相关数据。', 'items': found}

def table(year, url):
    matches = [x for x in catalog(year)['items'] if x['url'] == url]
    if len(matches) != 1:
        raise ValueError('URL not in selected yearbook index')
    soup = BeautifulSoup(_get(url), 'html.parser')
    out = []
    for table in soup.select('table'):
        rows = []
        for tr in table.find_all('tr'):
            if tr.find_parent('table') is not table:
                continue
            cells = tr.find_all(['td', 'th'], recursive=False)
            rows.append([{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in cells])
        if len(rows) >= 3:
            out.append(rows)
    if not out:
        raise ValueError('no HTML tables found')
    return {'source': '国家统计局中国统计年鉴', 'yearbook_year': year, 'title': matches[0]['title'], 'url': url, 'tables': out, 'note': '保留原始表格和合并信息；统计年、单位与范围以原表说明为准，空白不能视为零。'}
