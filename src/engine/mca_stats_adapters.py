"""民政部旧站统计公报目录及网页正文，只读。"""
import release_runtime
import argparse, json, re, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from research import fetch
BASE = 'https://www.mca.gov.cn/n156/n189/index.html'

class Listing(HTMLParser):

    def __init__(self):
        super().__init__()
        self.items = []
        self.current = None
        self.date = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        h = a.get('href', '').strip()
        title = a.get('title', '').strip()
        if tag == 'a' and re.match('\\d{4}年.*统计公报', title) and h:
            self.current = {'title': title, 'url': urljoin(BASE, h), 'date': ''}
            self.items.append(self.current)
        if tag == 'td' and 'timedefault' in a.get('class', '').split():
            self.date = True

    def handle_data(self, s):
        if self.date and self.current:
            self.current['date'] += s.strip()

    def handle_endtag(self, tag):
        if tag == 'td':
            self.date = False

class Article(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.found = False
        self.text = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if not self.depth and tag == 'div' and (a.get('id') == 'zoom'):
            self.depth = 1
            self.found = True
            return
        if self.depth and tag == 'div':
            self.depth += 1
        if self.depth and tag in ('p', 'br'):
            self.text.append('\n')

    def handle_data(self, s):
        if self.depth:
            self.text.append(s)

    def handle_endtag(self, tag):
        if self.depth and tag == 'div':
            self.depth -= 1

def mca_stats_list(keyword=''):
    p = Listing()
    p.feed(fetch(BASE))
    if not p.items:
        raise ValueError('未识别旧站公报目录')
    return {'source': '民政部旧站社会服务统计公报', 'source_url': BASE, 'items': [x for x in p.items if keyword in x['title']], 'note': '历史资料；本页不保证最新公报完整，PDF 需打开原件。'}

def mca_stats_detail(url):
    x = urlsplit(url)
    if x.scheme != 'https' or x.netloc != 'www.mca.gov.cn' or x.query or x.fragment or (not re.fullmatch('/n156/n189/c\\d+/content\\.html', x.path)):
        raise ValueError('只支持目录中的民政部旧站 HTML 公报地址')
    p = Article()
    p.feed(fetch(url))
    if not p.found:
        raise ValueError('未识别公报正文')
    return {'source_url': url, 'text': ''.join(p.text).strip(), 'note': '历史年度数据；表格和注释以原文为准。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('url')
    a = p.parse_args()
    print(json.dumps(mca_stats_list(a.keyword) if a.cmd == 'list' else mca_stats_detail(a.url), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或页面结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
