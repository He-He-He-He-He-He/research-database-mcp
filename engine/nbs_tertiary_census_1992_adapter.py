"""first national tertiary industry census: official NBS catalog and HTML tables."""
import release_runtime
import re
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.stats.gov.cn/sj/pcsj/scpc/dycscpc/'

def _get(url):
    with requests.get(url, timeout=(10, 45), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        data = bytearray()
        for chunk in r.iter_content(65536):
            data.extend(chunk)
            if len(data) > 5000000:
                raise ValueError('document too large')
        return bytes(data)

def catalog(page=0, keyword=''):
    if type(page) is not int or page != 0:
        raise ValueError('page must be 0')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    url = BASE + ('index.html' if page == 0 else f'index_{page}.html')
    soup = BeautifulSoup(_get(url), 'html.parser')
    items = []
    seen = set()
    for a in soup.select('a[href]'):
        u = urljoin(url, a['href'])
        parts = urlsplit(u)
        title = a.get('title', '').strip()
        if parts.scheme != 'https' or parts.netloc != 'www.stats.gov.cn' or (not re.fullmatch('/sj/pcsj/scpc/dycscpc/202302/t20230221_\\d+\\.html', parts.path)) or parts.query or parts.fragment or (not title) or (u in seen):
            continue
        seen.add(u)
        if keyword in title:
            items.append({'title': title, 'url': u})
    if not seen:
        raise ValueError('no tertiary census entries found')
    return {'source': '国家统计局首次全国第三产业普查', 'page': page, 'page_count': 1, 'total_page_entries': len(seen), 'items': items}

def table(page, url, keyword='', limit=100, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 100 or type(limit) is not int or (not 1 <= limit <= 500) or (type(offset) is not int) or (offset < 0):
        raise ValueError('invalid keyword, limit or offset')
    entry = next((x for x in catalog(page)['items'] if x['url'] == url), None)
    if entry is None:
        raise ValueError('URL not in requested official catalog page')
    soup = BeautifulSoup(_get(url), 'html.parser')
    tables = [t for t in soup.select('table') if not t.find('table') and len(t.find_all('tr')) > 2]
    if not tables:
        raise ValueError('no HTML data table found')
    result = []
    for t in tables:
        rows = []
        for n, tr in enumerate(t.find_all('tr'), 1):
            if tr.find_parent('table') is not t:
                continue
            cells = [{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
            rows.append({'row': n, 'cells': cells})
        if any((existing['_all_rows'] == rows for existing in result)):
            continue
        filtered = [x for x in rows if ''.join(keyword.split()) in ''.join((''.join(c['text'].split()) for c in x['cells']))]
        result.append({'_all_rows': rows, 'total_rows': len(rows), 'matched_rows': len(filtered), 'headers': rows[:5], 'offset': offset, 'rows': filtered[offset:offset + limit], 'truncated': len(filtered) > offset + limit})
    for t in result:
        del t['_all_rows']
    return {'source': '国家统计局首次全国第三产业普查', 'title': entry['title'], 'url': url, 'tables': result, 'note': '原表含1991和1992年比较列、不同指标单位、续表和经济类型或行业分类，以原表头和说明为准。'}
