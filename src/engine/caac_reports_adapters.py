"""中国民航局年度民航发展报告目录，只读。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
BASE = 'https://www.caac.gov.cn/XXGK/XXGK/TJSJ/'
INDEX = BASE + 'index_1214.html'

def fetch(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True)
    if p.returncode:
        raise RuntimeError('上游请求失败（curl 状态 %d）' % p.returncode)
    return p.stdout.decode('utf-8')

class Catalog(HTMLParser):

    def __init__(self):
        super().__init__()
        self.items = []
        self.item = None
        self.parts = []

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        h = a.get('href', '')
        if t == 'a' and re.fullmatch('\\./\\d{6}/t\\d{8}_\\d+\\.html', h):
            self.item = {'path': h[2:], 'title': a.get('title', '').strip()}
            self.parts = []

    def handle_data(self, s):
        if self.item:
            self.parts.append(s)

    def handle_endtag(self, t):
        if t == 'a' and self.item:
            if not self.item['title']:
                self.item['title'] = ' '.join(''.join(self.parts).split())
            self.items.append(self.item)
            self.item = None

class Detail(HTMLParser):

    def __init__(self):
        super().__init__()
        self.title = ''
        self.in_appendix = 0
        self.links = []

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'meta' and a.get('name') == 'ArticleTitle':
            self.title = a.get('content', '')
        if t == 'div':
            if self.in_appendix:
                self.in_appendix += 1
            elif a.get('id') == 'id_tblAppendix':
                self.in_appendix = 1
        if self.in_appendix and t == 'a' and a.get('href'):
            self.links.append(a['href'])

    def handle_endtag(self, t):
        if t == 'div' and self.in_appendix:
            self.in_appendix -= 1

def caac_reports(keyword=''):
    p = Catalog()
    p.feed(fetch(INDEX))
    if not p.items:
        raise ValueError('未识别民航报告列表')
    return {'source': '中国民航局年度民航发展报告', 'source_url': INDEX, 'items': [dict(i, url=urljoin(BASE, i['path'])) for i in p.items if keyword in i['title']], 'note': '仅筛选当前公开列表标题，不含其他专题或页。'}

def caac_report_detail(path):
    if not re.fullmatch('\\d{6}/t\\d{8}_\\d+\\.html', path):
        raise ValueError('路径格式错误')
    match = [i for i in caac_reports()['items'] if i['path'] == path]
    if not match:
        raise ValueError('路径不在当前目录')
    url = match[0]['url']
    p = Detail()
    p.feed(fetch(url))
    attachments = []
    for link in p.links:
        u = urljoin(url, link)
        x = urlsplit(u)
        if x.scheme == 'https' and x.hostname == 'www.caac.gov.cn' and x.path.lower().endswith('.pdf'):
            attachments.append(u)
    if not p.title:
        raise ValueError('未识别详情标题')
    return {'source': '中国民航局年度民航发展报告', 'url': url, 'title': p.title, 'attachments': attachments, 'note': '只返回 PDF 附件地址；未自动下载或解析数值，无附件不代表正文为空。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(caac_reports(a.keyword) if a.cmd == 'list' else caac_report_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
