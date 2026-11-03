"""国家医保局政策法规目录和正文，只读单页。"""
import release_runtime
import argparse, json, re, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from research import fetch
BASE = 'https://www.nhsa.gov.cn/'

class Entry(HTMLParser):

    def __init__(self):
        super().__init__()
        self.title = ''
        self.url = ''
        self.span = False
        self.date = ''

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'a' and re.fullmatch('/art/\\d{4}/\\d{1,2}/\\d{1,2}/art_53_\\d+\\.html', a.get('href', '')):
            self.url = urljoin(BASE, a['href'])
            self.title = a.get('title', '')
        if tag == 'span':
            self.span = True

    def handle_data(self, s):
        if self.span:
            self.date += s

    def handle_endtag(self, tag):
        if tag == 'span':
            self.span = False

class Article(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.title = ''
        self.text = []
        self.attachments = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and a.get('name') == 'ArticleTitle':
            self.title = a.get('content', '')
        if not self.depth and tag == 'div' and (a.get('id') == 'zoom'):
            self.depth = 1
            return
        if self.depth:
            if tag == 'div':
                self.depth += 1
            if tag in ('p', 'br'):
                self.text.append('\n')
            if tag == 'a' and a.get('href', '').startswith('/module/download/downfile.jsp?'):
                self.attachments.append(urljoin(BASE, a['href']))

    def handle_data(self, s):
        if self.depth:
            self.text.append(s)

    def handle_endtag(self, tag):
        if self.depth and tag == 'div':
            self.depth -= 1

def nhsa_policy_list(keyword=''):
    source = fetch(BASE + 'col/col53/index.html')
    entries = re.findall('<record><!\\[CDATA\\[(.*?)\\]\\]></record>', source, re.S)
    items = []
    for entry in entries:
        p = Entry()
        p.feed(entry)
        if p.url and p.title and (keyword in p.title):
            items.append({'title': p.title, 'date': p.date.strip(), 'url': p.url})
    if not entries:
        raise ValueError('政策目录网页结构变化')
    return {'source': '国家医保局政策法规', 'source_url': BASE + 'col/col53/index.html', 'scope': '当前目录页；关键词只筛标题', 'items': items, 'note': '不是完整政策库检索或药品目录。'}

def nhsa_policy_detail(url):
    x = urlsplit(url)
    if x.scheme != 'https' or x.netloc != 'www.nhsa.gov.cn' or x.query or x.fragment or (not re.fullmatch('/art/\\d{4}/\\d{1,2}/\\d{1,2}/art_53_\\d+\\.html', x.path)):
        raise ValueError('只接受国家医保局政策法规详情地址')
    p = Article()
    p.feed(fetch(url))
    if not p.title or not p.text:
        raise ValueError('未识别政策正文')
    return {'source_url': url, 'title': p.title, 'text': ''.join(p.text).strip(), 'attachments': p.attachments, 'note': '效力和药品支付范围以官网最新目录及相关规定为准。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('url')
    a = p.parse_args()
    print(json.dumps(nhsa_policy_list(a.keyword) if a.cmd == 'list' else nhsa_policy_detail(a.url), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
