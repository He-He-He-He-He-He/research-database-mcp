"""国家医疗保障局统计数据目录与公开正文。"""
import release_runtime
import argparse, html, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urlsplit, urljoin
BASE = 'https://www.nhsa.gov.cn'
INDEX = BASE + '/col/col7/'

def fetch(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True)
    if p.returncode:
        raise RuntimeError('上游请求失败（curl 状态 %d）' % p.returncode)
    return p.stdout.decode('utf-8')

class Body(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.parts = []
        self.title = ''
        self.images = []

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'meta' and a.get('name') == 'ArticleTitle':
            self.title = a.get('content', '')
        if t == 'div':
            if self.depth:
                self.depth += 1
            elif a.get('id') == 'zoom':
                self.depth = 1
        if self.depth and t in ('p', 'br', 'tr'):
            self.parts.append('\n')
        if self.depth and t in ('td', 'th'):
            self.parts.append('\t')
        if self.depth and t == 'img' and a.get('src'):
            self.images.append(a['src'])

    def handle_data(self, s):
        if self.depth:
            self.parts.append(s)

    def handle_endtag(self, t):
        if t == 'div' and self.depth:
            self.depth -= 1

def nhsa_statistics(keyword=''):
    text = fetch(INDEX)
    pairs = re.findall('<a\\s+href="(/art/\\d{4}/\\d{1,2}/\\d{1,2}/art_7_\\d+\\.html)"\\s+title="([^"]+)"', text)
    if not pairs:
        raise ValueError('未识别医保统计列表')
    items = []
    seen = set()
    for path, title in pairs:
        title = html.unescape(title)
        if path not in seen and keyword in title:
            items.append({'path': path, 'title': title, 'url': BASE + path})
            seen.add(path)
    return {'source': '国家医疗保障局统计数据', 'source_url': INDEX, 'items': items, 'note': '筛选当前首页内嵌目录标题，非医保全站、个人账户或全部历史统计。'}

def nhsa_statistic_detail(path):
    matches = [i for i in nhsa_statistics()['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在当前首页')
    url = matches[0]['url']
    p = Body()
    p.feed(fetch(url))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if not p.title or not text:
        raise ValueError('未识别统计正文')
    images = []
    for i in p.images:
        u = urljoin(url, i)
        x = urlsplit(u)
        if x.scheme == 'https' and x.hostname == 'www.nhsa.gov.cn':
            images.append(u)
    return {'source': '国家医疗保障局统计数据', 'title': p.title, 'url': url, 'text': text, 'images': images, 'note': '文字保留统计说明；图片不做 OCR，表格与口径请核对原文。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(nhsa_statistics(a.keyword) if a.cmd == 'list' else nhsa_statistic_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
