"""Read-only dynasty and material-type browsing for ZJU epigraph catalogue."""
import release_runtime
import re
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
from zju_tomb_api import BASE, Parser

def categories(timeout=20):
    r = requests.get(BASE + 'stone', timeout=timeout)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    result = {'dynasty': [], 'stone_type': []}
    for a in s.select('a[href^="stone/list?"]'):
        p = parse_qs(urlparse(a['href']).query)
        tag = p.get('tag', [None])[0]
        kind, key = ('dynasty', 'dynasty') if tag == '1' else ('stone_type', 'stoneType') if tag == '2' else (None, None)
        if kind and len(p.get(key, [])) == 1:
            name = p[key][0]
            if name and name not in result[kind]:
                result[kind].append(name)
    if not result['dynasty'] or not result['stone_type']:
        raise ValueError('category list not recognized')
    return result

def _validate_page(total, pages, page, items):
    if total < 0 or pages < 0 or (total > 0 and (pages != (total + 14) // 15 or page > pages)) or (len(items) != min(15, max(0, total - (page - 1) * 15))):
        raise ValueError('墓志目录总数、页数与题录数不一致')

def browse(kind, value, page=1, timeout=20):
    if kind not in ('dynasty', 'stone_type'):
        raise ValueError('kind must be dynasty or stone_type')
    if not isinstance(value, str) or value not in categories(timeout)[kind]:
        raise ValueError('value must be in current source categories')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('page must be 1–1000')
    params = {'tag': '1' if kind == 'dynasty' else '2', 'dynasty': value if kind == 'dynasty' else '', 'stoneType': value if kind == 'stone_type' else '', 'pageNumber': page, 'pageSize': 15}
    r = requests.get(BASE + 'stone/list', params=params, timeout=timeout)
    r.raise_for_status()
    p = Parser()
    p.feed(r.content.decode('utf-8'))
    text = ''.join(p.text)
    total = re.search('記錄數\\s*:\\s*(\\d+)', text)
    pager = re.search('(\\d+)\\s*/\\s*(\\d+)\\s*頁', text)
    if not total or not pager or int(pager.group(1)) != page:
        raise ValueError('result page not recognized')
    pages = int(pager.group(2))
    count = int(total.group(1))
    _validate_page(count, pages, page, p.rows)
    return {'source': '浙江大学中国历代墓志数据库', 'kind': kind, 'value': value, 'page': page, 'pages': pages, 'total': count, 'items': p.rows, 'note': '站方目录数据可能重复；仅题录，不读取图像或录文；上游 HTTP。'}
