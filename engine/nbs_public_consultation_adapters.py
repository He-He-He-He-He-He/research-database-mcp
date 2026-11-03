"""国家统计局咨询公开栏目当前页及问答详情。"""
import release_runtime
import re
import requests
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from szse_chinext_adapters import _Links
BASE = 'https://www.stats.gov.cn/hd/lyzx/zxgk/'
PATTERN = re.compile('/hd/lyzx/zxgk/\\d{6}/t\\d{8}_\\d+\\.html')

class _Answers(HTMLParser):

    def __init__(self):
        super().__init__()
        self.current = None
        self.parts = {}

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            key = dict(attrs).get('id')
            if key in ('tjsj', 'zxnr', 'dfnr', 'dfdw', 'dfsj'):
                self.current = key
                self.parts[key] = []

    def handle_data(self, s):
        if self.current:
            self.parts[self.current].append(s)

    def handle_endtag(self, tag):
        if tag == 'a':
            self.current = None

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.stats.gov.cn' or p.query or p.fragment or (not (p.path == '/hd/lyzx/zxgk/' or re.fullmatch('/hd/lyzx/zxgk/index_\\d+\\.html', p.path) or PATTERN.fullmatch(p.path))):
        raise ValueError('仅支持国家统计局咨询公开栏目')
    r = requests.get(url, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    r.encoding = 'utf-8'
    return r.text

def nbs_consultations(keyword=''):
    if not isinstance(keyword, str):
        raise ValueError('关键词须为字符串')
    p = _Links()
    p.feed(_get(BASE))
    out = []
    seen = set()
    recognized = False
    for href, title in p.links:
        url = urljoin(BASE, href)
        q = urlparse(url)
        title = ' '.join(title.split())
        if q.hostname == 'www.stats.gov.cn' and (not q.query) and (not q.fragment) and PATTERN.fullmatch(q.path) and title:
            recognized = True
            if keyword in title and url not in seen:
                seen.add(url)
                out.append({'title': title, 'url': url})
    if not recognized:
        raise ValueError('未识别目录，无法确认检索结果')
    return out

def nbs_consultations_page(page=1, keyword=''):
    if not isinstance(page, int) or isinstance(page, bool) or (not 1 <= page <= 10000) or (not isinstance(keyword, str)):
        raise ValueError('页码或关键词无效')
    url = BASE if page == 1 else BASE + f'index_{page - 1}.html'
    html = _get(url)
    m = re.search('createPageHTML\\(\\s*(\\d+)\\s*,\\s*(\\d+)\\s*,\\s*["\\\']index["\\\']\\s*,\\s*["\\\']html["\\\']\\s*\\)', html)
    if not m or int(m.group(2)) != page - 1:
        raise ValueError('来源页码或分页信息无法核验')
    pages = int(m.group(1))
    p = _Links()
    p.feed(html)
    out = []
    seen = set()
    for href, title in p.links:
        u = urljoin(BASE, href)
        q = urlparse(u)
        title = ' '.join(title.split())
        if q.scheme == 'https' and q.hostname == 'www.stats.gov.cn' and (not q.query) and (not q.fragment) and PATTERN.fullmatch(q.path) and title and (u not in seen):
            seen.add(u)
            if keyword in title:
                out.append({'title': title, 'url': u})
    if not seen or page > pages:
        raise ValueError('未识别目录，无法确认检索结果')
    return {'source': '国家统计局公开咨询', 'source_url': url, 'page': page, 'source_pages': pages, 'source_page_items': len(seen), 'keyword': keyword, 'items': out, 'note': '仅筛选本页标题；公开咨询答复针对当时问题和制度，须核对现行规则。'}

def nbs_consultations_search_pages(keyword='', start_page=1, end_page=3):
    if not isinstance(keyword, str) or any((not isinstance(x, int) or isinstance(x, bool) for x in (start_page, end_page))) or (not 1 <= start_page <= end_page <= 10000) or (end_page - start_page >= 20):
        raise ValueError('关键词或页码范围无效，每次最多 20 页')
    items = []
    sources = []
    seen = set()
    pages = None
    for page in range(start_page, end_page + 1):
        r = nbs_consultations_page(page)
        sources.append(r['source_url'])
        if pages is None:
            pages = r['source_pages']
        elif pages != r['source_pages']:
            raise ValueError('来源总页数变化，请重新查询')
        for item in r['items']:
            if item['url'] in seen:
                raise ValueError('跨页出现重复链接，目录可能更新；请重新查询')
            seen.add(item['url'])
            if keyword in item['title']:
                items.append(item)
    return {'source': '国家统计局公开咨询', 'keyword': keyword, 'start_page': start_page, 'end_page': end_page, 'source_pages': pages, 'source_urls': sources, 'matched_count': len(items), 'items': items, 'note': '仅筛选指定页标题，不代表全部历史；目录动态变化，跨页非原子快照。公开答复针对当时问题和制度，须核对现行规则。'}

def nbs_consultation_detail(url):
    p = _Answers()
    p.feed(_get(url))
    values = {k: ' '.join(''.join(v).split()) for k, v in p.parts.items()}
    if not values.get('zxnr') or not values.get('dfnr'):
        raise ValueError('未识别咨询及答复')
    return {'url': url, 'submitted': values.get('tjsj'), 'question': values['zxnr'], 'answer': values['dfnr'], 'responding_unit': values.get('dfdw'), 'answered': values.get('dfsj'), 'note': '公开咨询答复；仅适用于答复所述问题及其当时制度，请核对最新统计制度。'}
