"""生态环境部执法制度与行政处罚栏目，只读。"""
import release_runtime
import argparse, json, re, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from research import fetch
BASE = 'https://www.mee.gov.cn'
PATH = '/ywgz/sthjzf/zfzdyxzcf/'

class Listing(HTMLParser):

    def __init__(self):
        super().__init__()
        self.active = False
        self.items = []
        self.date = False
        self.anchor = False
        self.current = {}

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'ul' and a.get('id') == 'div':
            self.active = True
        elif self.active and t == 'li':
            self.current = {'date': '', 'title': '', 'url': ''}
        elif self.active and t == 'span' and ('date' in a.get('class', '').split()):
            self.date = True
        elif self.active and t == 'a':
            self.current['url'] = urljoin(BASE + PATH, a.get('href', ''))
            self.anchor = True

    def handle_data(self, d):
        if self.active and self.date:
            self.current['date'] += d.strip()
        if self.active and self.anchor:
            self.current['title'] += d.strip()

    def handle_endtag(self, t):
        if t == 'span':
            self.date = False
        if t == 'a':
            self.anchor = False
        if self.active and t == 'li' and self.current.get('url'):
            self.items.append(self.current)
            self.current = {}
        if t == 'ul' and self.active:
            self.active = False

class Article(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.seen = False
        self.parts = []

    def handle_starttag(self, t, attrs):
        if t == 'div' and (not self.depth) and ('content_body_box' in dict(attrs).get('class', '').split()):
            self.depth = 1
            self.seen = True
            return
        if self.depth:
            if t == 'div':
                self.depth += 1
            if t in ('p', 'br'):
                self.parts.append('\n')

    def handle_data(self, d):
        if self.depth:
            self.parts.append(d)

    def handle_endtag(self, t):
        if t == 'div' and self.depth:
            self.depth -= 1
        if t == 'p' and self.depth:
            self.parts.append('\n')

class NoticeArticle(Article):

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.resources = []

    def handle_starttag(self, t, attrs):
        if self.depth and t == 'a':
            href = dict(attrs).get('href', '')
            link = urljoin(self.url, href)
            u = urlparse(link)
            if href and u.scheme == 'https' and (u.netloc == 'www.mee.gov.cn') and (not u.query) and (not u.fragment) and re.search('\\.(?:pdf|docx?|xlsx?|zip)$', u.path, re.I):
                self.resources.append(link)
        super().handle_starttag(t, attrs)

def list_articles(page=1, keyword=''):
    if not 1 <= page <= 100:
        raise ValueError('页码须为 1 至 100')
    url = BASE + PATH + ('index.shtml' if page == 1 else 'index_' + str(page - 1) + '.shtml')
    p = Listing()
    p.feed(fetch(url))
    if not p.items:
        raise ValueError('未找到列表，可能页码超出或上游改版')
    return {'source': url, 'page': page, 'total_on_page': len(p.items), 'scope': '只筛选当前页标题；栏目同时包含征求意见和典型案例', 'items': [x for x in p.items if keyword.casefold() in x['title'].casefold()]}

def search_pages(keyword='', start_page=1, end_page=3):
    if not isinstance(keyword, str):
        raise ValueError('关键词须为字符串')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (start_page, end_page))) or not 1 <= start_page <= end_page <= 100 or end_page - start_page >= 20:
        raise ValueError('起止页须为 1–100 整数，最多查询连续 20 页')
    items = []
    sources = []
    seen = set()
    for page in range(start_page, end_page + 1):
        result = list_articles(page, keyword)
        sources.append(result['source'])
        for item in result['items']:
            if item['url'] in seen:
                raise ValueError('跨页出现重复链接，目录可能更新；请重新查询')
            seen.add(item['url'])
            items.append(item)
    return {'keyword': keyword, 'start_page': start_page, 'end_page': end_page, 'source_urls': sources, 'matched_count': len(items), 'items': items, 'scope': '仅筛选指定页标题，含征求意见稿、案例与正式文件；法律效力和现行状态须另核。目录动态变化，跨页非原子快照，不代表全历史。'}

def detail(url):
    u = urlparse(url)
    if u.scheme != 'https' or u.netloc != 'www.mee.gov.cn' or (not re.fullmatch('/xxgk2018/xxgk/xxgk03/\\d{6}/t\\d{8}_\\d+\\.html', u.path)) or u.query or u.fragment:
        raise ValueError('正文只支持生态环境部此栏目政府信息公开的处罚文书链接')
    p = Article()
    p.feed(fetch(url))
    if not p.seen:
        raise ValueError('未发现正文，可能上游改版')
    return {'source': url, 'text': ''.join(p.parts).strip()}

def notice_detail(url):
    u = urlparse(url)
    if u.scheme != 'https' or u.netloc != 'www.mee.gov.cn' or (not re.fullmatch('/xxgk2018/xxgk/xxgk0[56]/\\d{6}/t\\d{8}_\\d+\\.html', u.path)) or u.query or u.fragment:
        raise ValueError('仅支持生态环境部政府信息公开 xxgk05/06 正文链接')
    p = NoticeArticle(url)
    p.feed(fetch(url))
    if not p.seen:
        raise ValueError('未发现正文，可能上游改版')
    return {'source': url, 'text': ''.join(p.parts).strip(), 'resources': list(dict.fromkeys(p.resources)), 'note': '正文及原站附件链接；本接口未读取附件内容。附件可能包含正式规定、征求意见稿或说明，应逐项确认，现行效力另核。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('--page', type=int, default=1)
    q.add_argument('--keyword', default='')
    q = s.add_parser('search-pages')
    q.add_argument('--keyword', default='')
    q.add_argument('--start-page', type=int, default=1)
    q.add_argument('--end-page', type=int, default=3)
    q = s.add_parser('detail')
    q.add_argument('url')
    q = s.add_parser('notice-detail')
    q.add_argument('url')
    a = p.parse_args()
    print(json.dumps(list_articles(a.page, a.keyword) if a.cmd == 'list' else search_pages(a.keyword, a.start_page, a.end_page) if a.cmd == 'search-pages' else notice_detail(a.url) if a.cmd == 'notice-detail' else detail(a.url), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
