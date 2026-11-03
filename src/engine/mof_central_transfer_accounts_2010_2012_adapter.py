"""MOF 2010–2012 central expenditure and intergovernmental transfers, official HTML tables."""
import release_runtime
import re
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
INDEX = {2010: ['https://yss.mof.gov.cn/2010juesuan/index.htm', 'https://yss.mof.gov.cn/2010juesuan/index_1.htm', 'https://yss.mof.gov.cn/2010juesuan/index_2.htm'], 2011: ['https://yss.mof.gov.cn/2011qgczjs/index.htm', 'https://yss.mof.gov.cn/2011qgczjs/index_1.htm', 'https://yss.mof.gov.cn/2011qgczjs/index_2.htm'], 2012: ['https://yss.mof.gov.cn/2012qhczjs/index.htm', 'https://yss.mof.gov.cn/2012qhczjs/index_1.htm', 'https://yss.mof.gov.cn/2012qhczjs/index_2.htm']}
PREFIX = {2010: '/2010juesuan/', 2011: '/2011qgczjs/', 2012: '/2012qhczjs/'}

def _get(url):
    with requests.get(url, timeout=(10, 40), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        data = bytearray()
        for chunk in r.iter_content(65536):
            data.extend(chunk)
            if len(data) > 5000000:
                raise ValueError('source too large')
        return bytes(data)

def catalog(year, keyword=''):
    if type(year) is not int or year not in INDEX:
        raise ValueError('year must be 2010–2012')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    out = []
    seen = set()
    for index in INDEX[year]:
        soup = BeautifulSoup(_get(index), 'html.parser')
        for a in soup.select('a[href]'):
            title = ' '.join(a.get_text(' ', strip=True).split())
            u = urljoin(index, a['href'])
            p = urlsplit(u)
            if not title.startswith(f'{year}年') or not ('中央本级支出' in title or '中央对地方税收返还和转移支付' in title) or '政府性基金' in title or (not title.endswith('决算表')):
                continue
            if p.scheme != 'https' or p.netloc != 'yss.mof.gov.cn' or (not p.path.startswith(PREFIX[year])) or (not re.fullmatch('/[A-Za-z0-9_./-]+\\.htm', p.path)) or p.query or p.fragment or (u in seen):
                continue
            seen.add(u)
            if keyword in title:
                out.append({'title': title, 'url': u})
    if not seen:
        raise ValueError('no central accounts tables found')
    return {'source': '财政部中央本级及对地方税收返还和转移支付决算', 'year': year, 'total': len(seen), 'items': out}

def table(year, url, keyword='', limit=100, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 100 or type(limit) is not int or (not 1 <= limit <= 500) or (type(offset) is not int) or (offset < 0):
        raise ValueError('invalid keyword, limit or offset')
    entries = [x for x in catalog(year)['items'] if x['url'] == url]
    if len(entries) != 1:
        raise ValueError('URL not in selected official index')
    soup = BeautifulSoup(_get(url), 'html.parser')
    tables = [t for t in soup.select('table') if len(t.find_all('tr')) > 5]
    if len(tables) != 1:
        raise ValueError('expected exactly one data table')
    result = []
    for n, tr in enumerate(tables[0].find_all('tr'), 1):
        if tr.find_parent('table') is not tables[0]:
            continue
        cells = [{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
        result.append({'row': n, 'cells': cells})
    matched = [x for x in result if keyword in ' '.join((c['text'] for c in x['cells']))]
    return {'source': '财政部中央本级及对地方税收返还和转移支付决算', 'year': year, 'title': entries[0]['title'], 'url': url, 'total_rows': len(result), 'matched_rows': len(matched), 'headers': result[:5], 'offset': offset, 'rows': matched[offset:offset + limit], 'truncated': len(matched) > offset + limit, 'note': '保留原表单元格及合并属性。中央本级支出与对地方税收返还和转移支付为不同范围，预算和决算列不能混同。'}
