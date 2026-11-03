"""国家体育总局全国体育场地调查公告：目录、附件与可提取的 PDF 文本。"""
import release_runtime
import argparse, io, json, re, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
import requests
from pypdf import PdfReader
BASE = 'https://www.sport.gov.cn'
INDEX = BASE + '/jjs/n5043/index.html'

def fetch(url):
    if urlsplit(url).scheme != 'https' or urlsplit(url).hostname != 'www.sport.gov.cn':
        raise ValueError('仅允许体育总局 HTTPS 地址')
    r = requests.get(url, timeout=25, allow_redirects=False)
    r.raise_for_status()
    if len(r.content) > 20000000:
        raise ValueError('文件过大')
    return r

class Index(HTMLParser):

    def __init__(self):
        super().__init__()
        self.items = {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        t = a.get('title', '').strip()
        u = urljoin(INDEX, a.get('href', ''))
        p = urlsplit(u)
        if tag == 'a' and p.hostname == 'www.sport.gov.cn' and re.fullmatch('/jjs/n5043/c\\d+/content\\.html', p.path) and re.match('^20\\d\\d\\s*年全国体育场地统计调查数据$', t):
            self.items[t] = {'year': int(t[:4]), 'title': t, 'url': u}

class Body(HTMLParser):

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.inside = 0
        self.parts = []
        self.attachments = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'table':
            if self.inside:
                self.inside += 1
            elif a.get('id') == 'zoom':
                self.inside = 1
        if self.inside and tag in ('a', 'img'):
            u = urljoin(self.url, a.get('href' if tag == 'a' else 'src', ''))
            p = urlsplit(u)
            if p.scheme == 'https' and p.hostname == 'www.sport.gov.cn' and re.search('\\.(pdf|jpg|jpeg|png)$', p.path, re.I):
                self.attachments.append({'type': p.path.rsplit('.', 1)[-1].lower(), 'url': u})

    def handle_data(self, s):
        if self.inside:
            self.parts.append(s)

    def handle_endtag(self, tag):
        if tag == 'table' and self.inside:
            self.inside -= 1

def venue_list():
    p = Index()
    p.feed(fetch(INDEX).content.decode('utf-8'))
    if not p.items:
        raise ValueError('未识别公告目录')
    return {'source': '国家体育总局体育经济司', 'source_url': INDEX, 'items': sorted(p.items.values(), key=lambda x: -x['year']), 'note': '当前栏目首页；不是完整体育设施数据库。'}

def venue_report(year):
    rows = [x for x in venue_list()['items'] if x['year'] == int(year)]
    if not rows:
        raise ValueError('年份未在当前目录首页')
    item = rows[0]
    p = Body(item['url'])
    p.feed(fetch(item['url']).content.decode('utf-8'))
    pages = []
    for a in p.attachments:
        if a['type'] == 'pdf':
            pdf = PdfReader(io.BytesIO(fetch(a['url']).content))
            pages += [{'pdf_page': i + 1, 'text': page.extract_text() or ''} for i, page in enumerate(pdf.pages)]
    return {'source': '国家体育总局体育经济司', **item, 'page_text': ' '.join(' '.join(p.parts).split()), 'attachments': p.attachments, 'pdf_pages': pages, 'note': '图片附件不含可搜索文本；PDF 提取不包括图表图片。核对原件及调查口径，统计标准时点通常为当年12月31日。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='command', required=True)
    s.add_parser('list')
    q = s.add_parser('report')
    q.add_argument('year', type=int)
    a = p.parse_args()
    print(json.dumps(venue_list() if a.command == 'list' else venue_report(a.year), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
