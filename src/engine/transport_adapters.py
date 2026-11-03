"""交通运输部全国城市客运量月度发布目录，只读。"""
import release_runtime
import argparse, json, re, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from research import fetch
BASE = 'https://www.mot.gov.cn/shuju/tongjishuju/chengshikeyun/'

class Listing(HTMLParser):

    def __init__(self):
        super().__init__()
        self.url = None
        self.parts = []
        self.items = {}
        self.section = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        v = a.get('href', '')
        if tag == 'section' and 'news-list-section' in a.get('class', '').split():
            self.section = True
        if self.section and tag == 'a' and re.fullmatch('https://xxgk\\.mot\\.gov\\.cn/jigou/zhghs/\\d{6}/t\\d{8}_\\d+\\.html', v):
            self.url = v
            self.parts = []

    def handle_data(self, s):
        if self.url:
            self.parts.append(s)

    def handle_endtag(self, tag):
        if tag == 'section':
            self.section = False
        if tag == 'a' and self.url:
            title = re.sub('\\s+\\d{4}-\\d{2}-\\d{2}$', '', ' '.join(''.join(self.parts).split()))
            if '全国城市客运量' in title:
                self.items[self.url] = {'title': title, 'url': self.url}
            self.url = None

class Attach(HTMLParser):

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.title = ''
        self.files = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and a.get('name') == 'ArticleTitle':
            self.title = a.get('content', '')
        if tag == 'a' and re.fullmatch('\\./P\\d+\\.(?:xlsx|xls|pdf)', a.get('href', ''), re.I):
            self.files.add(urljoin(self.url, a['href']))

def transport_list(page=1, keyword=''):
    if not 1 <= page <= 100:
        raise ValueError('页码应为 1–100')
    u = BASE if page == 1 else BASE + 'index_' + str(page - 1) + '.html'
    p = Listing()
    p.feed(fetch(u))
    if not p.items:
        raise ValueError('未识别到客运量目录；可能超出页码或网站改版')
    return {'source': '交通运输部', 'source_url': u, 'page': page, 'items': [x for x in p.items.values() if keyword in x['title']], 'note': '仅当前目录页标题筛选。'}

def transport_detail(url):
    x = urlsplit(url)
    if x.scheme != 'https' or x.netloc != 'xxgk.mot.gov.cn' or x.query or x.fragment or (not re.fullmatch('/jigou/zhghs/\\d{6}/t\\d{8}_\\d+\\.html', x.path)):
        raise ValueError('仅支持本模块目录返回的交通部公开页面')
    p = Attach(url)
    p.feed(fetch(url))
    if not p.files:
        raise ValueError('未找到统计表附件；可能页面改版')
    return {'source_url': url, 'title': p.title, 'attachment_urls': sorted(p.files), 'note': '未下载或解析附件数据，单位和统计口径请以官方附件为准。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('--page', type=int, default=1)
    q.add_argument('--keyword', default='')
    q = s.add_parser('detail')
    q.add_argument('url')
    a = p.parse_args()
    print(json.dumps(transport_list(a.page, a.keyword) if a.cmd == 'list' else transport_detail(a.url), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
