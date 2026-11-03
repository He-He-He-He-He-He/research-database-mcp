"""国家审计署报告及解读栏目，只读。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
BASE = 'https://www.audit.gov.cn'
INDEX = BASE + '/n5/n26/index.html'

def fetch(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True)
    if p.returncode:
        raise RuntimeError('上游请求失败（curl 状态 %d）' % p.returncode)
    return p.stdout.decode('utf-8')

class Catalog(HTMLParser):

    def __init__(self):
        super().__init__()
        self.items = {}

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        url = urljoin(INDEX, a.get('href', ''))
        x = urlsplit(url)
        title = a.get('title', '').strip()
        if t == 'a' and title and (x.hostname == 'www.audit.gov.cn') and re.fullmatch('/n5/n26/c\\d+/content\\.html', x.path):
            self.items[x.path] = {'path': x.path, 'title': title, 'url': BASE + x.path}

class Body(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.title = ''
        self.parts = []
        self.links = []

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'meta' and a.get('name') == 'ArticleTitle':
            self.title = a.get('content', '')
        if t == 'div':
            if self.depth:
                self.depth += 1
            elif a.get('id') == 'textSize':
                self.depth = 1
        if self.depth and t in ('p', 'br', 'tr'):
            self.parts.append('\n')
        if self.depth and t == 'a' and a.get('href'):
            self.links.append(a['href'])

    def handle_data(self, s):
        if self.depth:
            self.parts.append(s)

    def handle_endtag(self, t):
        if t == 'div' and self.depth:
            self.depth -= 1

def audit_reports(keyword=''):
    p = Catalog()
    p.feed(fetch(INDEX))
    if not p.items:
        raise ValueError('未识别审计报告目录')
    return {'source': '审计署报告及解读', 'source_url': INDEX, 'items': [i for i in p.items.values() if keyword in i['title']], 'note': '当前栏目首页标题筛选，不是全部审计结果或全站搜索。'}

def audit_report_detail(path):
    matches = [i for i in audit_reports()['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在当前目录首页')
    url = matches[0]['url']
    p = Body()
    p.feed(fetch(url))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if not p.title or not text:
        raise ValueError('未识别详情')
    links = []
    for link in p.links:
        u = urljoin(url, link)
        x = urlsplit(u)
        if x.scheme == 'https' and x.hostname == 'www.audit.gov.cn' and x.path.lower().endswith('.pdf'):
            links.append(u)
    return {'source': '审计署报告及解读', 'title': p.title, 'url': url, 'text': text, 'pdf_links': links, 'note': '报告有时仅以 PDF 发布；仅返回链接，不解析附件。文字与表格请核对原文。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(audit_reports(a.keyword) if a.cmd == 'list' else audit_report_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
