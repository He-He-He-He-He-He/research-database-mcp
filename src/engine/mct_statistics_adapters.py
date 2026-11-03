"""文化和旅游部统计信息公开目录与正文，只读。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
INDEX = 'https://zwgk.mct.gov.cn/zfxxgkml/447/465/index_3081.html'
BASE = 'https://zwgk.mct.gov.cn'

def fetch(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True)
    if p.returncode:
        raise RuntimeError('上游请求失败（curl 状态 %d）' % p.returncode)
    return p.stdout.decode('utf-8')

class Catalog(HTMLParser):

    def __init__(self):
        super().__init__()
        self.href = None
        self.parts = []
        self.items = []

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        u = urljoin(INDEX, a.get('href', ''))
        x = urlsplit(u)
        if t == 'a' and x.hostname == 'zwgk.mct.gov.cn' and re.fullmatch('/zfxxgkml/tjxx/\\d{6}/t\\d{8}_\\d+\\.html', x.path):
            self.href = x.path
            self.parts = []

    def handle_data(self, s):
        if self.href:
            self.parts.append(s)

    def handle_endtag(self, t):
        if t == 'a' and self.href:
            title = ' '.join(''.join(self.parts).split())
            if title:
                self.items.append({'title': title, 'path': self.href, 'url': BASE + self.href})
            self.href = None

class Body(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.skip = 0
        self.parts = []
        self.images = []
        self.published = ''

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'meta' and a.get('name') == 'PubDate':
            self.published = a.get('content', '')
        if t == 'div':
            if self.depth:
                self.depth += 1
            elif 'gsj_htmlcon_bot' in a.get('class', '').split():
                self.depth = 1
        if self.depth and t in ('style', 'script'):
            self.skip += 1
        if self.depth and (not self.skip) and (t in ('p', 'br', 'div', 'tr')):
            self.parts.append('\n')
        if self.depth and (not self.skip) and (t in ('td', 'th')):
            self.parts.append('\t')
        if self.depth and t == 'img' and a.get('src'):
            self.images.append(a['src'])

    def handle_data(self, s):
        if self.depth and (not self.skip):
            self.parts.append(s)

    def handle_endtag(self, t):
        if self.depth and t in ('style', 'script') and self.skip:
            self.skip -= 1
        if self.depth and t == 'div':
            self.depth -= 1

def mct_statistics(keyword=''):
    p = Catalog()
    p.feed(fetch(INDEX))
    if not p.items:
        raise ValueError('未识别统计目录')
    return {'source': '文化和旅游部统计信息', 'source_url': INDEX, 'items': [i for i in p.items if keyword in i['title']], 'note': '仅筛选当前统计信息目录标题，不是全站搜索或结构化表格。'}

def mct_statistics_detail(path):
    matches = [i for i in mct_statistics()['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在当前统计目录')
    url = matches[0]['url']
    p = Body()
    p.feed(fetch(url))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if not text:
        raise ValueError('未识别正文')
    images = []
    for i in p.images:
        u = urljoin(url, i)
        x = urlsplit(u)
        if x.scheme == 'https' and x.hostname == 'zwgk.mct.gov.cn':
            images.append(u)
    return {'source': '文化和旅游部统计信息', 'url': url, 'title': matches[0]['title'], 'published': p.published, 'text': text, 'images': images, 'note': '正文表格只抽取文字，图表返回图片链接，统计口径请以原文为准。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(mct_statistics(a.keyword) if a.cmd == 'list' else mct_statistics_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
