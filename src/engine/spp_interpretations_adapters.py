"""最高人民检察院司法解释栏目。"""
import release_runtime
import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, urlunsplit
from spp_typical_cases_adapters import _get, _Body
BASE = 'https://www.spp.gov.cn/spp/flfg/sfjs/'

class _List(HTMLParser):

    def __init__(self, base=BASE):
        super().__init__()
        self.base = base
        self.inside = False
        self.item = None
        self.field = None
        self.rows = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'ul' and 'li_line' in attrs.get('class', '').split():
            self.inside = True
        if not self.inside:
            return
        if tag == 'li':
            self.item = {'title': '', 'date': '', 'url': ''}
        if self.item is not None and tag == 'a':
            self.item['url'] = urljoin(self.base, attrs.get('href', ''))
            self.field = 'title'
        if self.item is not None and tag == 'span':
            self.field = 'date'

    def handle_data(self, text):
        if self.item is not None and self.field:
            self.item[self.field] += text

    def handle_endtag(self, tag):
        if tag in ('a', 'span'):
            self.field = None
        if tag == 'li' and self.item is not None:
            p = urlsplit(self.item['url'])
            if p.scheme == 'https' and p.hostname == 'www.spp.gov.cn' and p.path.endswith('.shtml'):
                self.item['title'] = ' '.join(self.item['title'].split())
                self.item['date'] = self.item['date'].strip()
                self.rows.append(self.item)
            self.item = None
        if tag == 'ul' and self.inside:
            self.inside = False

def spp_interpretations_list(page=1, keyword=''):
    page = int(page)
    if not 1 <= page <= 100:
        raise ValueError('页码应为 1—100')
    url = BASE + ('index.shtml' if page == 1 else f'index_{page}.shtml')
    parser = _List()
    parser.feed(_get(url))
    if not parser.rows:
        raise ValueError('未找到目录；页码可能超出范围或网站改版')
    return {'page': page, 'source_url': url, 'scope': '关键词只筛选当前页标题；历史文书效力及最新修订需另行核查。', 'items': [row for row in parser.rows if keyword.casefold() in row['title'].casefold()]}

def spp_interpretations_search_pages(keyword='', start_page=1, end_page=3):
    if not isinstance(keyword, str):
        raise ValueError('关键词须为字符串')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (start_page, end_page))) or not 1 <= start_page <= end_page <= 100 or end_page - start_page >= 20:
        raise ValueError('起止页须为 1–100 的整数，最多查询连续 20 页')
    items = []
    sources = []
    seen = set()
    for page in range(start_page, end_page + 1):
        result = spp_interpretations_list(page, keyword)
        sources.append(result['source_url'])
        for item in result['items']:
            if item['url'] in seen:
                raise ValueError('跨页出现重复链接，目录可能已更新；请重新查询')
            seen.add(item['url'])
            items.append(item)
    return {'keyword': keyword, 'start_page': start_page, 'end_page': end_page, 'source_urls': sources, 'matched_count': len(items), 'items': items, 'scope': '仅筛选所选页标题，不保证完整历史；目录动态变化，跨页非原子快照。栏目可能包含发布会或解读，效力和修订须核验。'}

def spp_interpretations_search_all(keyword='', limit=30, offset=0):
    if not isinstance(keyword, str):
        raise ValueError('关键词须为字符串')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (limit, offset))) or not 1 <= limit <= 100 or (not 0 <= offset <= 100000):
        raise ValueError('limit 须为 1–100，offset 须为 0–100000')

    def source_page(page):
        url = BASE + ('index.shtml' if page == 1 else f'index_{page}.shtml')
        html = _get(url)
        m = re.search('createPageHTML\\(\\s*[\'\\"]page_div[\'\\"]\\s*,\\s*(\\d+)\\s*,\\s*(\\d+)\\s*,\\s*[\'\\"]index[\'\\"]\\s*,\\s*[\'\\"]shtml[\'\\"]\\s*,\\s*(\\d+)\\s*\\)', html)
        if not m or int(m.group(2)) != page:
            raise ValueError('来源页码或分页信息无法核验')
        p = _List()
        p.feed(html)
        if not p.rows:
            raise ValueError('未识别来源司法解释目录')
        return (int(m.group(1)), int(m.group(3)), p.rows)
    pages, total, first = source_page(1)
    if not 1 <= pages <= 20 or not 0 <= total <= 2000:
        raise ValueError('目录超过本次遍历上限')
    rows = []
    seen = set()
    for page in range(1, pages + 1):
        p, t, items = (pages, total, first) if page == 1 else source_page(page)
        if (p, t) != (pages, total):
            raise ValueError('来源目录分页或总数变化')
        for item in items:
            if item['url'] in seen:
                raise ValueError('跨页出现重复来源链接')
            seen.add(item['url'])
            rows.append(item)
    if len(rows) != total:
        raise ValueError('来源目录总数与解析条目不一致')
    matches = [row for row in rows if keyword in row['title']]
    selected = matches[offset:offset + limit]
    return {'source': '最高人民检察院司法解释栏目', 'keyword': keyword, 'source_pages': pages, 'source_total': total, 'matched_count': len(matches), 'offset': offset, 'limit': limit, 'next_offset': offset + len(selected) if offset + len(selected) < len(matches) else None, 'items': selected, 'note': '逐页读取当前栏目并筛选标题，保留原始 URL 和锚点；目录动态更新，跨页非原子快照，偏移可能变化。栏目可能包含发布会及解读，现行效力和修订须另核。'}

def spp_interpretations_detail(url):
    p = urlsplit(url)
    if p.scheme != 'https' or p.hostname != 'www.spp.gov.cn' or p.query or (not re.fullmatch('/+(?:[\\w-]+/)*t\\d{8}_\\d+\\.shtml', p.path)):
        raise ValueError('仅允许最高检官网公开文章链接')
    clean = urlunsplit(('https', 'www.spp.gov.cn', '/' + p.path.lstrip('/'), '', ''))
    parser = _Body()
    parser.feed(_get(clean))
    text = '\n'.join((line.strip() for line in ''.join(parser.parts).splitlines() if line.strip()))
    if len(text) < 100:
        raise ValueError('未识别正文')
    return {'source_url': url, 'article_url': clean, 'anchor': p.fragment, 'text': text, 'note': '返回完整文章而非锚点对应片段；栏目可能含发布会合集及解读，现行效力和修订须核验。'}
