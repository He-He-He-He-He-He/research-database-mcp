"""国家新闻出版署政策法规目录：部门规章、规范性文件。"""
import release_runtime
import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from nppa_statistics_adapters import fetch
from szse_chinext_adapters import _Links
ROOT = 'https://www.nppa.gov.cn/xxgk/fdzdgknr/zcfg_210/'
CATEGORIES = {'rules': 'bmgz_213', 'normative': 'gfxwj_215'}

def nppa_regulations_list(category='rules', page=1, keyword=''):
    page = int(page)
    if category not in CATEGORIES or not 1 <= page <= 100:
        raise ValueError('分类须为 rules 或 normative，页码为 1—100')
    base = ROOT + CATEGORIES[category] + '/'
    url = base + ('index.html' if page == 1 else f'index_{page - 1}.html')
    parser = _Links()
    parser.feed(fetch(url).decode('utf-8'))
    rows = []
    source_items = 0
    for href, title in parser.links:
        link = urljoin(base, href)
        if re.fullmatch(re.escape(base) + '\\d{6}/t\\d{8}_\\d+\\.html', link):
            source_items += 1
            title = ' '.join(title.split())
            if keyword.casefold() in title.casefold():
                rows.append({'title': title, 'url': link})
    if not source_items:
        raise ValueError('未识别目录，可能超出页数、被重定向或网站改版；不能认定无匹配')
    return {'category': category, 'page': page, 'source_url': url, 'items': rows, 'scope': '只筛选当前页标题；目录可能含历史版本，效力状态须另行核查。'}

def nppa_regulations_search_pages(category='rules', keyword='', start_page=1, end_page=2):
    if category not in CATEGORIES or not isinstance(keyword, str):
        raise ValueError('分类或关键词无效')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (start_page, end_page))) or not 1 <= start_page <= end_page <= 100 or end_page - start_page >= 20:
        raise ValueError('起止页须为 1–100 的整数，最多查询连续 20 页')
    items = []
    sources = []
    seen = set()
    for page in range(start_page, end_page + 1):
        result = nppa_regulations_list(category, page, keyword)
        sources.append(result['source_url'])
        for item in result['items']:
            if item['url'] in seen:
                raise ValueError('跨页出现重复链接，目录可能已更新；请重新查询')
            seen.add(item['url'])
            items.append(item)
    return {'category': category, 'keyword': keyword, 'start_page': start_page, 'end_page': end_page, 'source_urls': sources, 'matched_count': len(items), 'items': items, 'scope': '仅筛选指定栏目页面标题；目录动态更新，跨页并非原子快照，不代表全部历史。历史版本的现行效力及后续修订需另核。'}

class _Body(HTMLParser):

    def __init__(self, target):
        super().__init__()
        self.target = target
        self.depth = 0
        self.text = []
        self.found = False
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            if self.depth:
                self.depth += 1
            elif self.target in dict(attrs).get('class', '').split():
                self.depth = 1
                self.found = True
        if self.depth and tag in ('script', 'style'):
            self.skip += 1
        if self.depth and (not self.skip) and (tag in ('p', 'br', 'h2')):
            self.text.append('\n')

    def handle_data(self, text):
        if self.depth and (not self.skip):
            self.text.append(text)

    def handle_endtag(self, tag):
        if self.depth and tag in ('script', 'style') and self.skip:
            self.skip -= 1
        if tag == 'div' and self.depth:
            self.depth -= 1

def nppa_regulations_detail(url):
    p = urlsplit(url)
    if p.scheme != 'https' or p.hostname != 'www.nppa.gov.cn' or p.query or p.fragment or (not re.fullmatch('/xxgk/fdzdgknr/zcfg_210/(?:bmgz_213|gfxwj_215)/\\d{6}/t\\d{8}_\\d+\\.html', p.path)):
        raise ValueError('仅允许以上两个栏目内的官方文章')
    raw = fetch(url).decode('utf-8')
    target = 'gsj_htmlcon_bot' if re.search('class="gsj_htmlcon_bot"', raw) else 'gsj_htmlcon'
    parser = _Body(target)
    parser.feed(raw)
    text = '\n'.join((s.strip() for s in ''.join(parser.text).splitlines() if s.strip()))
    if not parser.found or len(text) < 100:
        raise ValueError('未识别正文')
    attachments = []
    for h in re.findall('["\\\'](\\./P\\d+\\.(?:pdf|docx?|xlsx?))["\\\']', raw, re.I):
        link = urljoin(url, h)
        if link not in attachments:
            attachments.append(link)
    return {'source_url': url, 'text': text, 'attachments': attachments, 'note': '历史发布文本不自动判断现行效力；附件只返回官方链接。'}
