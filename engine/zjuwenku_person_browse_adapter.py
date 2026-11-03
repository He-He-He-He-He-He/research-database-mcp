"""浙大文库求是学人目录普通分页。"""
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
    params = {'honorTypeId': '', 'sub': '', 'sp': '', 'pageNumber': str(page), 'pageSize': '20'}
    with urlopen(BASE + 'people?' + urlencode(params), timeout=20) as response:
        soup = BeautifulSoup(response.read().decode('utf-8'), 'html.parser')
    pager = soup.select_one('.m-page')
    if not pager or not soup.title or '求是学人' not in soup.title.get_text():
        raise RuntimeError('未识别求是学人分页')
    t = pager.get_text(' ', strip=True)
    m = re.search('(\\d+)\\s*/\\s*(\\d+)\\s*页\\s*共\\s*(\\d+)\\s*条记录', t)
    if not m or int(m.group(1)) != page:
        raise RuntimeError('请求页码与页面不符')
    items, seen = ([], set())
    for link in soup.select('a[href^="people/detail?"]'):
        name = link.get_text(' ', strip=True)
        href = link.get('href', '')
        q = parse_qs(urlsplit(href).query)
        ids = q.get('id', [])
        if not name or q.get('type') != ['0'] or len(ids) != 1 or (not re.fullmatch('[0-9a-fA-F]{32}', ids[0])) or (ids[0] in seen):
            continue
        seen.add(ids[0])
        items.append({'id': ids[0], 'name': name, 'url': urljoin(BASE, href)})
    if not items or len(items) > 20:
        raise RuntimeError('目录记录未识别或数量异常')
    validate_page_count(int(m.group(3)), int(m.group(2)), page, items, 20)
    return {'source': '浙大文库求是学人', 'page': page, 'pages': int(m.group(2)), 'total': int(m.group(3)), 'items': items, 'note': '仅求是学人目录当前页姓名及编号；不包含人物正文、照片，原站数据与分类可能变化。上游 HTTP。'}
