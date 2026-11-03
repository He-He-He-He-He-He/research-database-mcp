"""最高人民检察院典型案例栏目。"""
import release_runtime
import re
import subprocess
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, urlsplit, urlunsplit
from szse_chinext_adapters import _Links
BASE = 'https://www.spp.gov.cn'
INDEX = BASE + '/spp/zgjdxal/'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.spp.gov.cn' or p.query or p.fragment:
        raise ValueError('仅允许最高检官网公开网页')
    return release_runtime.run(['curl', '--compressed', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout.decode('utf-8')

class _Body(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.skip = 0
        self.parts = []

    def handle_starttag(self, t, attrs):
        if t == 'div':
            if self.depth:
                self.depth += 1
            elif dict(attrs).get('id') == 'fontzoom':
                self.depth = 1
        if self.depth and t in ('style', 'script'):
            self.skip += 1
        if self.depth and (not self.skip) and (t in ('p', 'br', 'h2')):
            self.parts.append('\n')

    def handle_data(self, s):
        if self.depth and (not self.skip):
            self.parts.append(s)

    def handle_endtag(self, t):
        if self.depth and t in ('style', 'script') and self.skip:
            self.skip -= 1
        if t == 'div' and self.depth:
            self.depth -= 1

def spp_cases(keyword=''):
    if not isinstance(keyword, str):
        raise ValueError('关键词须为字符串')
    p = _Links()
    p.feed(_get(INDEX))
    out = []
    seen = set()
    recognized = False
    for href, title in p.links:
        x = urlparse(urljoin(INDEX, href))
        path = '/' + x.path.lstrip('/')
        if x.hostname == 'www.spp.gov.cn' and re.fullmatch('/(?:spp/)?xwfbh/\\w+/\\d{6}/t\\d{8}_\\d+\\.shtml', path) and title:
            recognized = True
            if keyword in title and path not in seen:
                seen.add(path)
                out.append({'title': title, 'url': BASE + path})
    if not recognized:
        raise ValueError('未识别案例目录，无法确认检索结果')
    return out

class _CasePage(HTMLParser):

    def __init__(self):
        super().__init__()
        self.inside = False
        self.row = None
        self.field = None
        self.rows = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'ul' and 'li_line' in attrs.get('class', '').split():
            self.inside = True
        elif self.inside and tag == 'li':
            self.row = {'title': '', 'date': '', 'source_href': ''}
        elif self.row is not None and tag == 'a':
            self.row['source_href'] = attrs.get('href', '')
            self.field = 'title'
        elif self.row is not None and tag == 'span':
            self.field = 'date'

    def handle_data(self, text):
        if self.row is not None and self.field:
            self.row[self.field] += text

    def handle_endtag(self, tag):
        if tag in ('a', 'span'):
            self.field = None
        if tag == 'li' and self.row is not None:
            self.row['title'] = ' '.join(self.row['title'].split())
            self.row['date'] = self.row['date'].strip()
            self.rows.append(self.row)
            self.row = None
        if tag == 'ul' and self.inside:
            self.inside = False

def spp_cases_page(page=1, keyword=''):
    if not isinstance(page, int) or isinstance(page, bool) or (not 1 <= page <= 10000) or (not isinstance(keyword, str)):
        raise ValueError('页码或关键词无效')
    url = INDEX + ('index.shtml' if page == 1 else f'index_{page}.shtml')
    html = _get(url)
    m = re.search('createPageHTML\\(\\s*[\'\\"]page_div[\'\\"]\\s*,\\s*(\\d+)\\s*,\\s*(\\d+)\\s*,\\s*[\'\\"]index[\'\\"]\\s*,\\s*[\'\\"]shtml[\'\\"]\\s*,\\s*(\\d+)\\s*\\)', html)
    if not m or int(m.group(2)) != page:
        raise ValueError('来源页码或分页信息无法核验')
    pages, total = (int(m.group(1)), int(m.group(3)))
    p = _CasePage()
    p.feed(html)
    if not p.rows or page > pages:
        raise ValueError('未识别来源案例目录')
    items = []
    for row in p.rows:
        if not row['title']:
            raise ValueError('来源目录缺少标题')
        if keyword not in row['title']:
            continue
        original = row['source_href']
        u = urlsplit(urljoin(INDEX, original))
        path = '/' + u.path.lstrip('/')
        valid = u.scheme == 'https' and u.netloc == 'www.spp.gov.cn' and (not u.query) and bool(re.fullmatch('/(?:[\\w-]+/)*t\\d{8}_\\d+\\.shtml', path))
        items.append({'title': row['title'], 'date': row['date'], 'source_href': original, 'article_url': urlunsplit(('https', 'www.spp.gov.cn', path, '', '')) if valid else None, 'anchor': u.fragment if valid else None, 'valid_article_url': valid})
    return {'source': '最高人民检察院典型案例栏目', 'source_url': url, 'page': page, 'source_pages': pages, 'source_total': total, 'source_page_items': len(p.rows), 'keyword': keyword, 'items': items, 'note': '保留来源链接和锚点；无有效官方文章链接的标题仍保留，但不能自动读取。列表项可为案例合集，非单案全集；原文及后续状态须核。'}

def spp_cases_search_all(keyword='', limit=30, offset=0):
    if not isinstance(keyword, str):
        raise ValueError('关键词须为字符串')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (limit, offset))) or not 1 <= limit <= 100 or (not 0 <= offset <= 100000):
        raise ValueError('limit 须为 1–100，offset 须为 0–100000')
    first = spp_cases_page(1)
    pages = first['source_pages']
    total = first['source_total']
    if not 1 <= pages <= 20 or not 0 <= total <= 2000:
        raise ValueError('目录超过本次遍历上限')
    rows = []
    seen = set()
    for n in range(1, pages + 1):
        r = first if n == 1 else spp_cases_page(n)
        if r['source_pages'] != pages or r['source_total'] != total or r['source_page_items'] != len(r['items']):
            raise ValueError('来源目录分页或总数变化')
        for item in r['items']:
            key = (item['article_url'], item['anchor']) if item['valid_article_url'] else (None, item['source_href'])
            if key in seen:
                raise ValueError('跨页出现重复链接或来源地址')
            seen.add(key)
            rows.append(item)
    if len(rows) != total:
        raise ValueError('来源目录总数与解析条目不一致')
    matches = [row for row in rows if keyword in row['title']]
    selected = matches[offset:offset + limit]
    return {'source': '最高人民检察院典型案例栏目', 'keyword': keyword, 'source_pages': pages, 'source_total': total, 'matched_count': len(matches), 'offset': offset, 'limit': limit, 'next_offset': offset + len(selected) if offset + len(selected) < len(matches) else None, 'items': selected, 'note': '逐页读取当前栏目并筛选标题；目录动态更新，跨页非原子快照，偏移可能变化。保留源链接和锚点，无效链接不自动读取；条目可为案例合集，非所有案件。'}

def spp_case_detail(url):
    p = _Body()
    p.feed(_get(url))
    text = '\n'.join((s.strip() for s in ''.join(p.parts).splitlines() if s.strip()))
    if len(text) < 100:
        raise ValueError('未识别案例正文')
    return {'url': url, 'text': text, 'note': '仅公开典型案例发布文本，非裁判文书全集，也非所有案件；请核对原文和案件后续状态。'}
