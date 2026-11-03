"""交通运输部公路水路运输量数据发布目录，只读。"""
import release_runtime
import argparse, json, re, sys
from html.parser import HTMLParser
from research import fetch
from transport_adapters import transport_detail
BASE = 'https://www.mot.gov.cn/shuju/tongjishuju/gonglushuilu/'

class Listing(HTMLParser):

    def __init__(self):
        super().__init__()
        self.section = False
        self.url = None
        self.buf = []
        self.items = {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        u = a.get('href', '')
        if tag == 'section' and 'news-list-section' in a.get('class', '').split():
            self.section = True
        if self.section and tag == 'a' and re.fullmatch('https://xxgk\\.mot\\.gov\\.cn/jigou/zhghs/\\d{6}/t\\d{8}_\\d+\\.html', u):
            self.url = u
            self.buf = []

    def handle_data(self, s):
        if self.url:
            self.buf.append(s)

    def handle_endtag(self, tag):
        if tag == 'section':
            self.section = False
        if tag == 'a' and self.url:
            title = re.sub('\\s+\\d{4}-\\d{2}-\\d{2}$', '', ' '.join(''.join(self.buf).split()))
            if '公路水路运输量' in title:
                self.items[self.url] = {'title': title, 'url': self.url}
            self.url = None

def freight_list(page=1, keyword=''):
    if not 1 <= page <= 100:
        raise ValueError('页码必须为 1–100')
    u = BASE if page == 1 else BASE + 'index_' + str(page - 1) + '.html'
    p = Listing()
    p.feed(fetch(u))
    if not p.items:
        raise ValueError('未识别公路水路运输数据目录')
    return {'source': '交通运输部公路水路运输量', 'source_url': u, 'page': page, 'items': [x for x in p.items.values() if keyword in x['title']], 'note': '当前目录页标题筛选；不是货运经营业户或车辆登记数据库。'}

def freight_detail(url):
    d = transport_detail(url)
    d['note'] = '官方统计表附件链接；未解析或下载附件，单位及口径以原件为准。'
    return d

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('--page', type=int, default=1)
    q.add_argument('--keyword', default='')
    q = s.add_parser('detail')
    q.add_argument('url')
    a = p.parse_args()
    print(json.dumps(freight_list(a.page, a.keyword) if a.cmd == 'list' else freight_detail(a.url), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或页面结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
