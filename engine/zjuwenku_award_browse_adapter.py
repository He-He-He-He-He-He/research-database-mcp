"""浙大文库获奖作品题名搜索与分页。"""
import release_runtime
import re
from urllib.parse import urlencode, urljoin, urlsplit, parse_qs
from urllib.request import urlopen
from bs4 import BeautifulSoup
from zjuwenku_api import BASE
from zjuwenku_page_counts import validate_page_count

def search(keyword='', page=1, field='title'):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词须为最多100字')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为1–1000')
    fields = {'title': '题名', 'author': '作者', 'publishTime': '出版年', 'awardName': '奖项名称', 'callNo': '索书号', 'awardTime': '获奖年', 'subject': '所属学科'}
    if field not in fields:
        raise ValueError('不支持的检索字段')
    keyword = keyword.strip()
    params = {'keyword1': keyword, 'property1': field, 'pageNumber': str(page), 'pageSize': '10'}
    with urlopen(BASE + 'award?' + urlencode(params), timeout=20) as response:
        soup = BeautifulSoup(response.read().decode('utf-8'), 'html.parser')
    pager = soup.select_one('.m-page')
    input_field = soup.select_one('input[name="keyword1"]')
    selected = soup.select_one('select[name="property1"] option[selected]')
    if not soup.title or '获奖作品' not in soup.title.get_text() or (not input_field) or (input_field.get('value', '') != keyword) or (not selected) or (selected.get('value') != field):
        raise RuntimeError('未识别获奖作品检索页或关键词')
    if not pager and page == 1 and ('没有找到记录' in soup.get_text(' ', strip=True)):
        return {'source': '浙大文库获奖作品', 'keyword': keyword, 'field': fields[field], 'page': page, 'pages': 0, 'total': 0, 'items': [], 'note': '原站明确显示没有找到记录；仅限浙大文库获奖作品。上游 HTTP。'}
    if not pager:
        raise RuntimeError('未识别分页；可能页码超出范围或页面发生变化')
    m = re.search('(\\d+)\\s*/\\s*(\\d+)\\s*页\\s*共\\s*(\\d+)\\s*条记录', pager.get_text(' ', strip=True))
    if not m or int(m.group(1)) != page:
        raise RuntimeError('请求页码与页面不符')
    items = []
    seen = set()
    for link in soup.select('a[href^="award/detail?"]'):
        text = link.get_text(' ', strip=True)
        q = parse_qs(urlsplit(link.get('href', '')).query)
        ids = q.get('id', [])
        if not text.startswith('题名：') or len(ids) != 1 or (not re.fullmatch('[0-9a-fA-F]{32}', ids[0])) or (ids[0] in seen):
            continue
        seen.add(ids[0])
        items.append({'id': ids[0], 'title': text.removeprefix('题名：').strip(), 'url': urljoin(BASE, link['href'])})
    if not items or len(items) > 10:
        raise RuntimeError('未识别当前页作品：可能无结果或页面变化')
    validate_page_count(int(m.group(3)), int(m.group(2)), page, items, 10)
    return {'source': '浙大文库获奖作品', 'keyword': keyword, 'field': fields[field], 'page': page, 'pages': int(m.group(2)), 'total': int(m.group(3)), 'items': items, 'note': '仅当前页作品题录，不保证与所有浙大获奖作品一致；获奖信息请查询详情，不含全文或图片。上游 HTTP。'}
