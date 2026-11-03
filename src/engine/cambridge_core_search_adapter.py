"""剑桥 Core 官方公开网页搜索题录，非学校机构或全文权限验证。"""
import release_runtime
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
URL = 'https://www.cambridge.org/core/search'

def search(keyword, page=1):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 150:
        raise ValueError('关键词须为 1–150 字')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为 1–1000')
    r = requests.get(URL, params={'q': keyword.strip(), 'pageNum': page}, timeout=20)
    r.raise_for_status()
    s = BeautifulSoup(r.text, 'html.parser')
    title = s.select_one('h1.title')
    if not title or 'Search Results' not in title.get_text(' ', strip=True):
        raise RuntimeError('未识别剑桥搜索页面，可能有访问限制或格式变化')
    pagination = [x.get_text(' ', strip=True) for x in s.select('p.paragraph_05')]
    match = next((re.search('Page\\s+(\\d+)\\s+of\\s+([\\d,]+)', x) for x in pagination if re.search('Page\\s+(\\d+)\\s+of\\s+([\\d,]+)', x)), None)
    if not match or int(match.group(1)) != page:
        raise RuntimeError('未核实结果页码；空结果或网站格式可能不同')
    h = s.select_one('h2.title')
    total = re.match('([\\d,]+)\\s+results?\\s+for\\s+', h.get_text(' ', strip=True) if h else '')
    if not total:
        raise RuntimeError('未识别检索结果数')
    items = []
    for heading in s.select('h3'):
        a = heading.select_one('a[href]') or heading.find_parent('a', href=True)
        if not a:
            raise RuntimeError('题录标题缺少链接')
        href = a.get('href', '')
        name = heading.get_text(' ', strip=True)
        if not href.startswith('/core/') or not name:
            raise RuntimeError('题录链接异常')
        details = a.find_parent('ul', class_='details')
        authors = [v.get_text(' ', strip=True) for v in details.select('li.author a.more-by-this-author')] if details else []
        kind = details.select_one('li.type') if details else None
        items.append({'title': name, 'authors': authors, 'type': kind.get_text(' ', strip=True) if kind else None, 'url': urljoin('https://www.cambridge.org', href)})
    if not items:
        raise RuntimeError('未识别题录；空结果或页面结构可能不同')
    return {'source': 'Cambridge Core 官方公开搜索', 'query': keyword.strip(), 'page': page, 'pages': int(match.group(2).replace(',', '')), 'total': int(total.group(1).replace(',', '')), 'items': items, 'note': '公开搜索结果不等于浙大订购范围或全文权限；排序及数量可能变化，未读取全文。'}
