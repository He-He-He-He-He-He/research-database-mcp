"""无锡市司法局“复议决定书公开”栏目单页目录。"""
import release_runtime
import json, re, subprocess
from html.parser import HTMLParser
from urllib.parse import urljoin
BASE = 'https://wxsfj.wuxi.gov.cn'
PATH = '/ztzl/xzfy/fyjdsgk/'

class Listing(HTMLParser):

    def __init__(self):
        super().__init__()
        self.active = False
        self.item = None
        self.in_date = False
        self.items = []
        self.seen = False
        self.bad = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'ul' and 'list03' in a.get('class', '').split():
            self.active = True
            self.seen = True
        elif self.active and tag == 'li':
            self.item = {}
        elif self.active and self.item is not None and (tag == 'a'):
            href = a.get('href', '')
            title = a.get('title', '').strip()
            if re.fullmatch('/doc/\\d{4}/\\d{2}/\\d{2}/\\d+\\.shtml', href) and title:
                self.item.update(title=title, url=urljoin(BASE, href))
            else:
                self.bad += 1
        elif self.active and self.item is not None and (tag == 'span') and ('riqi' in a.get('class', '').split()):
            self.in_date = True

    def handle_data(self, data):
        if self.in_date and self.item is not None:
            self.item['published'] = data.strip()

    def handle_endtag(self, tag):
        if tag == 'span':
            self.in_date = False
        if self.active and tag == 'li' and (self.item is not None):
            if self.item.get('title') and self.item.get('url'):
                self.items.append(self.item)
            else:
                self.bad += 1
            self.item = None
        if self.active and tag == 'ul':
            self.active = False

def search(keyword='', page=1):
    if not 1 <= int(page) <= 1000:
        raise ValueError('页码必须是正整数')
    path = PATH + ('index.shtml' if int(page) == 1 else 'index_' + str(int(page)) + '.shtml')
    p = release_runtime.run(['curl', '--silent', '--show-error', '--fail', '--location', '--max-time', '25', BASE + path], capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError('目录请求失败，请核对页码或稍后重试: ' + p.stderr.strip())
    m = re.search('"pageIndex":"(\\d+)"\\s*,\\s*"pageCount":"(\\d+)"\\s*,\\s*"pageSize":"(\\d+)"', p.stdout)
    if not m or int(m.group(1)) != int(page):
        raise RuntimeError('页面未显示所请求页码，栏目结构可能已变化')
    parser = Listing()
    parser.feed(p.stdout)
    if not parser.seen or parser.bad:
        raise RuntimeError('栏目结果结构不完整，未返回局部结果')
    all_items = parser.items
    return {'source': '无锡市司法局复议决定书公开栏目', 'page': int(page), 'page_count': int(m.group(2)), 'page_size': int(m.group(3)), 'keyword': keyword, 'page_items': len(all_items), 'items': [x for x in all_items if keyword in x['title']], 'scope': '仅筛选指定栏目页的标题；不代表全部行政复议案件或全国文书；正文与现行法律效力需自行核对官方页面'}
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('keyword', nargs='?', default='')
    p.add_argument('--page', type=int, default=1)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.page), ensure_ascii=False, indent=2))
