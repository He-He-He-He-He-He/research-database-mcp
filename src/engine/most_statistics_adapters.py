"""科学技术部科技统计栏目，按公开年份目录查公报。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urljoin
BASE = 'https://www.most.gov.cn/xxgk/xinxifenlei/fdzdgknr/kjtjbg/'

def fetch(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True)
    if p.returncode:
        raise RuntimeError('上游请求失败（curl 状态 %d）' % p.returncode)
    return p.stdout.decode('utf-8')

class Index(HTMLParser):

    def __init__(self):
        super().__init__()
        self.items = []
        self.item = None
        self.buf = []

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        h = a.get('href', '')
        if t == 'a' and re.fullmatch('\\./\\d{6}/t\\d{8}_\\d+\\.html', h):
            self.item = {'path': h[2:], 'title': a.get('title', '').strip()}
            self.buf = []

    def handle_data(self, s):
        if self.item:
            self.buf.append(s)

    def handle_endtag(self, t):
        if t == 'a' and self.item:
            if not self.item['title']:
                self.item['title'] = ' '.join(''.join(self.buf).split())
            self.items.append(self.item)
            self.item = None

class Body(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.parts = []
        self.meta = {}
        self.skip = 0

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'meta' and a.get('name') in ('ArticleTitle', 'PubDate'):
            self.meta[a['name']] = a.get('content', '')
        if t == 'div':
            if self.depth:
                self.depth += 1
            elif 'html-content-fun' in a.get('class', '').split():
                self.depth = 1
        if self.depth and t in ('style', 'script'):
            self.skip += 1
        if self.depth and (not self.skip) and (t in ('p', 'br', 'tr')):
            self.parts.append('\n')
        if self.depth and (not self.skip) and (t in ('td', 'th')):
            self.parts.append('\t')

    def handle_data(self, s):
        if self.depth and (not self.skip):
            self.parts.append(s)

    def handle_endtag(self, t):
        if self.depth and t in ('style', 'script') and self.skip:
            self.skip -= 1
        if self.depth and t == 'div':
            self.depth -= 1

def most_stats(year, keyword=''):
    year = int(year)
    if not 2000 <= year <= 2100:
        raise ValueError('年份不合法')
    url = BASE + f'kjtj{year}/'
    p = Index()
    p.feed(fetch(url))
    return {'source': '科技部科技统计公开栏目', 'source_url': url, 'year': year, 'items': [dict(x, url=urljoin(url, x['path'])) for x in p.items if keyword in x['title']], 'note': '只筛选指定发布年份目录，空结果可能因目录无条目或页面结构变化；年份是目录发布年。'}

def most_stats_detail(year, path):
    year = int(year)
    if not re.fullmatch('\\d{6}/t\\d{8}_\\d+\\.html', path):
        raise ValueError('路径格式不正确')
    entries = most_stats(year)['items']
    match = [i for i in entries if i['path'] == path]
    if not match:
        raise ValueError('路径不在指定年份目录')
    p = Body()
    p.feed(fetch(match[0]['url']))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if not text or not p.meta.get('ArticleTitle'):
        raise ValueError('未识别公报正文')
    return {'source': '科技部科技统计公开栏目', 'url': match[0]['url'], 'title': p.meta['ArticleTitle'], 'published': p.meta.get('PubDate'), 'text': text, 'note': '正文包含表格时仅提取文本，不保证表格结构和脚注关系，请核对原文。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('year', type=int)
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('year', type=int)
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(most_stats(a.year, a.keyword) if a.cmd == 'list' else most_stats_detail(a.year, a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
