"""浙大文库动态列表分页。"""
import release_runtime
import re
from urllib.parse import urlencode, urljoin, urlsplit, parse_qs
from urllib.request import urlopen
from bs4 import BeautifulSoup
from zjuwenku_api import BASE
from zjuwenku_page_counts import validate_page_count

def browse(page=1):
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为1–1000')
    with urlopen(BASE + 'news?' + urlencode({'pageNumber': page}), timeout=20) as response:
        soup = BeautifulSoup(response.read().decode('utf-8'), 'html.parser')
    pager = soup.select_one('.m-page')
    if not pager or not soup.title or '文库动态' not in soup.title.get_text():
        raise RuntimeError('未识别文库动态页面')
    m = re.search('(\\d+)\\s*/\\s*(\\d+)\\s*页\\s*共\\s*(\\d+)\\s*条记录', pager.get_text(' ', strip=True))
    if not m or int(m.group(1)) != page:
        raise RuntimeError('请求页码与页面不符')
    items = []
    seen = set()
    for a in soup.select('a[href^="news/detail?"]'):
        title = a.get_text(' ', strip=True)
        ids = parse_qs(urlsplit(a.get('href', '')).query).get('id', [])
        if not title or len(ids) != 1 or (not re.fullmatch('[0-9a-fA-F]{32}', ids[0])) or (ids[0] in seen):
            continue
        seen.add(ids[0])
        items.append({'id': ids[0], 'title': title, 'url': urljoin(BASE, a['href'])})
    if not items or len(items) > 10:
        raise RuntimeError('未识别动态目录记录')
    validate_page_count(int(m.group(3)), int(m.group(2)), page, items, 10)
    return {'source': '浙大文库动态', 'page': page, 'pages': int(m.group(2)), 'total': int(m.group(3)), 'items': items, 'note': '仅当前页动态标题和编号，正文需单独读取；目录随网站更新。上游 HTTP。'}
