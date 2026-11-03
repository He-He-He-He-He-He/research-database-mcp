"""国家铁路局行业统计公开目录，只读。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
BASE = 'https://www.nra.gov.cn/xwzx/zlzx/hytj/'

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
        h = a.get('href', '')
        title = a.get('title', '').strip()
        if t == 'a' and title and re.fullmatch('\\./\\d{6}/t\\d{8}_\\d+\\.shtml', h):
            self.items[h[2:]] = {'path': h[2:], 'title': title, 'url': urljoin(BASE, h)}

class Body(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.parts = []
        self.media = []

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'div':
            if self.depth:
                self.depth += 1
            elif 'gksqxz_main_content' in a.get('class', '').split():
                self.depth = 1
        if self.depth and t in ('p', 'br', 'div', 'tr'):
            self.parts.append('\n')
        if self.depth and t == 'img' and a.get('src'):
            self.media.append(a['src'])
        if self.depth and t == 'a' and a.get('href'):
            self.media.append(a['href'])

    def handle_data(self, s):
        if self.depth:
            self.parts.append(s)

    def handle_endtag(self, t):
        if self.depth and t == 'div':
            self.depth -= 1

def railway_statistics(keyword=''):
    p = Catalog()
    p.feed(fetch(BASE))
    if not p.items:
        raise ValueError('未识别行业统计目录')
    return {'source': '国家铁路局行业统计', 'source_url': BASE, 'items': [i for i in p.items.values() if keyword in i['title']], 'note': '仅当前目录首页按标题筛选，非全站、全部历史或结构化数据。'}

def railway_statistic_detail(path):
    matches = [i for i in railway_statistics()['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在当前目录首页')
    url = matches[0]['url']
    p = Body()
    p.feed(fetch(url))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    media = []
    for link in p.media:
        u = urljoin(url, link)
        x = urlsplit(u)
        if x.scheme == 'https' and x.hostname == 'www.nra.gov.cn' and x.path.lower().endswith(('.jpg', '.jpeg', '.png', '.pdf')):
            media.append(u)
    if not text and (not media):
        raise ValueError('未识别统计详情文字或图表')
    return {'source': '国家铁路局行业统计', 'title': matches[0]['title'], 'url': url, 'text': text, 'media': media, 'note': '统计表可能为图片，返回链接不 OCR；正文为空不表示数据为空，请查看原图。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(railway_statistics(a.keyword) if a.cmd == 'list' else railway_statistic_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
