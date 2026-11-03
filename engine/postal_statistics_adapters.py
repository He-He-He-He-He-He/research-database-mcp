"""国家邮政局统计信息目录及正文，只读。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
BASE = 'https://www.spb.gov.cn'
INDEX = BASE + '/gjyzj/c100276/common_list.shtml'

def fetch(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True)
    if p.returncode:
        raise RuntimeError('上游请求失败（curl 状态 %d）' % p.returncode)
    return p.stdout.decode('utf-8')

class Catalog(HTMLParser):

    def __init__(self):
        super().__init__()
        self.active = False
        self.a = None
        self.tag = None
        self.items = []

    def handle_starttag(self, t, attrs):
        x = dict(attrs)
        if t == 'ul' and 'listul' in x.get('class', '').split():
            self.active = True
        if self.active and t == 'a' and x.get('href', '').startswith('/gjyzj/'):
            self.a = {'path': x['href'], 'title': '', 'published': ''}
        elif self.a and t in ('p', 'span'):
            self.tag = t

    def handle_data(self, s):
        if self.a and self.tag == 'p':
            self.a['title'] += s
        elif self.a and self.tag == 'span':
            self.a['published'] += s

    def handle_endtag(self, t):
        if t in ('p', 'span'):
            self.tag = None
        if t == 'a' and self.a:
            self.a['title'] = ' '.join(self.a['title'].split())
            self.a['published'] = self.a['published'].strip()
            if self.a['title']:
                self.items.append(self.a)
            self.a = None
        if t == 'ul' and self.active:
            self.active = False

class Body(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.parts = []
        self.title = ''
        self.in_title = False
        self.images = []

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'title':
            self.in_title = True
        if t == 'div':
            if self.depth:
                self.depth += 1
            elif 'detail-news' in a.get('class', '').split():
                self.depth = 1
        if self.depth and t in ('p', 'br', 'tr'):
            self.parts.append('\n')
        if self.depth and t in ('td', 'th'):
            self.parts.append('\t')
        if self.depth and t == 'img' and a.get('src'):
            self.images.append(a['src'])

    def handle_data(self, s):
        if self.in_title:
            self.title += s
        if self.depth:
            self.parts.append(s)

    def handle_endtag(self, t):
        if t == 'title':
            self.in_title = False
        if t == 'div' and self.depth:
            self.depth -= 1

def postal_statistics(keyword=''):
    p = Catalog()
    p.feed(fetch(INDEX))
    if not p.items:
        raise ValueError('未识别邮政统计列表')
    return {'source': '国家邮政局统计信息', 'source_url': INDEX, 'items': [dict(i, url=urljoin(BASE, i['path'])) for i in p.items if keyword in i['title']], 'note': '只筛选当前首页列表标题；不包括查看更多内其他页。'}

def postal_statistic_detail(path):
    if not re.fullmatch('/gjyzj/(?:c\\d+/)+\\d{6}/[0-9a-f]{32}\\.shtml', path):
        raise ValueError('路径格式不正确')
    matches = [i for i in postal_statistics()['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在当前列表')
    url = matches[0]['url']
    p = Body()
    p.feed(fetch(url))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if not p.title.strip() or not text:
        raise ValueError('未识别统计正文')
    images = []
    for i in p.images:
        u = urljoin(url, i)
        x = urlsplit(u)
        if x.scheme == 'https' and x.hostname == 'www.spb.gov.cn':
            images.append(u)
    return {'source': '国家邮政局统计信息', 'url': url, 'title': p.title.strip(), 'text': text, 'images': images, 'note': '表格为文字提取，不保证行列关系；图片返回链接。请核对原文统计口径。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(postal_statistics(a.keyword) if a.cmd == 'list' else postal_statistic_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
