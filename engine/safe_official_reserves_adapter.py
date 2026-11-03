"""国家外汇管理局官方储备资产跨年度公开原表。"""
import release_runtime
import re
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
PAGE = 'https://www.safe.gov.cn/safe/gfcbzc/index.html'

def _get(url):
    r = requests.get(url, timeout=25, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect or len(r.content) > 8000000:
        raise ValueError('响应重定向或过大')
    return BeautifulSoup(r.content, 'html.parser')

def years():
    s = _get(PAGE)
    items = {}
    for a in s.select('a[href]'):
        title = a.get_text(' ', strip=True)
        m = re.match('官方储备资产（(20\\d{2})', title)
        if not m:
            continue
        u = urljoin(PAGE, a['href'])
        p = urlsplit(u)
        if p.scheme == 'https' and p.hostname == 'www.safe.gov.cn' and re.fullmatch('/safe/\\d{4}/\\d{4}/\\d+\\.html', p.path):
            items.setdefault(m.group(1), {'year': int(m.group(1)), 'title': title, 'url': u})
    if not items:
        raise ValueError('官网未返回年表目录')
    return {'source': '国家外汇管理局', 'source_url': PAGE, 'items': sorted(items.values(), key=lambda x: x['year'], reverse=True)}

def table(year):
    if isinstance(year, bool) or not isinstance(year, int):
        raise ValueError('年份必须为整数')
    item = next((x for x in years()['items'] if x['year'] == year), None)
    if not item:
        raise ValueError('年份不在官方目录')
    s = _get(item['url'])
    candidates = []
    for t in s.select('table'):
        if '官方储备资产' not in t.get_text(' ', strip=True):
            continue
        rows = []
        for tr in t.find_all('tr'):
            cells = []
            for c in tr.find_all(['td', 'th'], recursive=False):
                cells.append({'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))})
            if cells:
                rows.append(cells)
        if rows:
            candidates.append(rows)
    if len(candidates) != 1:
        raise ValueError('未识别唯一官方储备资产表')
    return {'source': '国家外汇管理局', 'year': year, 'source_url': item['url'], 'table': candidates[0], 'note': '按原表保留多级表头与注释；金额有亿美元与亿 SDR 两种单位，黄金同时公布数量，月末存量不等于当月流量。'}
