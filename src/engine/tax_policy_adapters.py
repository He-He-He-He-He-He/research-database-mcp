"""国家税务总局政策法规库近期目录和正文，只读。"""
import release_runtime
import argparse, json, re, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from research import fetch
ROOT = 'https://fgk.chinatax.gov.cn'
LIST = ROOT + '/zcfgk/c100027/list.html'

class Listing(HTMLParser):

    def __init__(self):
        super().__init__()
        self.active = False
        self.field = None
        self.item = None
        self.items = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        href = a.get('href', '')
        if tag == 'a' and re.fullmatch('/zcfgk/c\\d+/c\\d+/content\\.html', href):
            self.active = True
            self.item = {'url': ROOT + href, 'title': '', 'document_number': '', 'date': ''}
        if self.active and tag == 'p':
            c = a.get('class', '')
            self.field = {'bt': 'title', 'fwzh': 'document_number', 'cwrq': 'date'}.get(c)

    def handle_data(self, s):
        if self.active and self.field:
            self.item[self.field] += s

    def handle_endtag(self, tag):
        if tag == 'p':
            self.field = None
        if tag == 'a' and self.active:
            if self.item['title'].strip():
                self.items.append({k: v.strip() for k, v in self.item.items()})
            self.active = False

class Article(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.found = False
        self.text = []
        self.status_on = False
        self.status = ''

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = a.get('class', '').split()
        if tag == 'span' and 'xg' in classes:
            self.status_on = True
        if not self.depth and tag == 'div' and ('arc_cont' in classes):
            self.depth = 1
            self.found = True
            return
        if self.depth and tag == 'div':
            self.depth += 1
        if self.depth and tag in ('p', 'br'):
            self.text.append('\n')

    def handle_data(self, s):
        if self.status_on:
            self.status += s
        if self.depth:
            self.text.append(s)

    def handle_endtag(self, tag):
        if tag == 'span':
            self.status_on = False
        if self.depth and tag == 'div':
            self.depth -= 1

def tax_policy_list(keyword=''):
    p = Listing()
    p.feed(fetch(LIST))
    if not p.items:
        raise ValueError('未识别近期政策文件目录')
    return {'source': '国家税务总局政策法规库', 'source_url': LIST, 'scope': '近期政策当前目录页，关键词只筛选标题', 'items': [x for x in p.items if keyword in x['title']], 'note': '不是全法规库检索；注意文件效力和当地执行规定。'}

def tax_policy_detail(url):
    x = urlsplit(url)
    if x.scheme != 'https' or x.netloc != 'fgk.chinatax.gov.cn' or x.query or x.fragment or (not re.fullmatch('/zcfgk/c\\d+/c\\d+/content\\.html', x.path)):
        raise ValueError('仅支持税务总局法规库详情地址')
    p = Article()
    p.feed(fetch(url))
    if not p.found:
        raise ValueError('未识别政策正文')
    return {'source_url': url, 'status_display': p.status.strip(), 'text': ''.join(p.text).strip(), 'note': '网页显示的状态可能随政策变化，实际适用日期和后续修订须核对官网。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('url')
    a = p.parse_args()
    print(json.dumps(tax_policy_list(a.keyword) if a.cmd == 'list' else tax_policy_detail(a.url), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
