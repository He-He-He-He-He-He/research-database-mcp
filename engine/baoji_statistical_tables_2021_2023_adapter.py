"""Baoji statistics bureau annual public HTML tables 2021–2023."""
import release_runtime
import hashlib, re
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
ROOT = 'https://tjj.baoji.gov.cn/col1925/col1948/'
YEARS = {2021: ('col17653', 3), 2022: ('col18393', 5), 2023: ('2023ntjsj', 4)}

def _get(url):
    with requests.get(url, stream=True, timeout=(10, 30), allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        data = bytearray()
        for c in r.iter_content(65536):
            data.extend(c)
            if len(data) > 3000000:
                raise ValueError('response too large')
    return bytes(data)

def catalog(year, keyword=''):
    if type(year) is not int or year not in YEARS:
        raise ValueError('available years: 2021–2023')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    folder, pages = YEARS[year]
    base = ROOT + folder + '/'
    items = []
    errors = []
    seen = set()
    for n in range(pages):
        page = base + ('index.html' if n == 0 else f'index_{n}.html')
        try:
            soup = BeautifulSoup(_get(page), 'html.parser')
            for a in soup.find_all('a', href=True):
                title = ' '.join(a.get_text(' ', strip=True).split())
                url = urljoin(page, a['href'])
                p = urlsplit(url)
                if f'【{year}】' not in title or p.scheme != 'https' or p.hostname != 'tjj.baoji.gov.cn' or (not re.fullmatch('/col1925/col1948/' + re.escape(folder) + '/\\d{6}/t\\d{8}_\\d+\\.html', p.path)):
                    continue
                id = p.path.rsplit('_', 1)[-1][:-5]
                if id not in seen:
                    seen.add(id)
                    if keyword in title:
                        items.append({'id': id, 'title': title, 'url': url})
        except (requests.RequestException, ValueError) as e:
            errors.append({'page': n, 'error': str(e)})
    return {'source': '宝鸡市统计局统计数据查询', 'year': year, 'items': items, 'count': len(items), 'errors': errors, 'note': '目录仅包括已配置的年份和分页；若errors非空则结果可能不完整。不同年度表名、范围和统计口径可能变化。'}

def table(year, table_id):
    if not isinstance(table_id, str) or not re.fullmatch('\\d+', table_id):
        raise ValueError('invalid table ID')
    listing = catalog(year)
    if listing['errors']:
        raise RuntimeError('catalog incomplete')
    match = [x for x in listing['items'] if x['id'] == table_id]
    if len(match) != 1:
        raise ValueError('ID not found or ambiguous')
    item = match[0]
    raw = _get(item['url'])
    soup = BeautifulSoup(raw, 'html.parser')
    tables = soup.find_all('table')
    if not tables:
        raise ValueError('no HTML table')
    t = max(tables, key=lambda v: len(v.find_all('tr')))
    rows = []
    for tr in t.find_all('tr'):
        rows.append([{'text': ' '.join(c.get_text(' ', strip=True).split()), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)])
    if len(rows) < 3:
        raise ValueError('table too small')
    return {'source': '宝鸡市统计局', 'year': year, 'id': table_id, 'title': item['title'], 'source_url': item['url'], 'source_sha256': hashlib.sha256(raw).hexdigest(), 'rows': rows, 'note': '返回原HTML表格及单元格合并信息；单位、时间、统计范围及原文注释以来源为准，不对跨年表格自动对齐。'}
