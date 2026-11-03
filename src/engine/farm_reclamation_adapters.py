"""农业农村部农垦局工作动态公开栏目，只读。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urljoin
BASE = 'https://nkj.moa.gov.cn/gzdt/'

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
        if t == 'a' and title and re.fullmatch('\\./\\d{6}/t\\d{8}_\\d+\\.htm', h):
            self.items[h[2:]] = {'path': h[2:], 'title': title, 'url': urljoin(BASE, h)}

class Body(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.skip = 0
        self.parts = []

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'div':
            if self.depth:
                self.depth += 1
            elif 'TRS_Editor' in a.get('class', '').split():
                self.depth = 1
        if self.depth and t in ('style', 'script'):
            self.skip += 1
        if self.depth and (not self.skip) and (t in ('p', 'br', 'div', 'tr')):
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

def farm_reclamation_list(keyword='', page=0):
    if not isinstance(page, int) or not 0 <= page <= 1000:
        raise ValueError('页码必须为 0 至 1000')
    url = BASE + ('index.htm' if page == 0 else f'index_{page}.htm')
    p = Catalog()
    p.feed(fetch(url))
    if not p.items:
        raise ValueError('未识别目录，页码可能超出范围或页面变化')
    return {'source': '农业农村部农垦局工作动态', 'source_url': url, 'page': page, 'items': [i for i in p.items.values() if keyword in i['title']], 'note': '仅筛选指定列表页标题，页码 0 为首页；非全站或结构化统计库。'}

def farm_reclamation_detail(path, page=0):
    matches = [i for i in farm_reclamation_list('', page)['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在指定页')
    p = Body()
    p.feed(fetch(matches[0]['url']))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if not text:
        raise ValueError('未识别正文')
    return {'source': '农业农村部农垦局工作动态', **matches[0], 'text': text, 'note': '仅提取正文文字，统计口径、图表与附件须核对原文。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q.add_argument('--page', type=int, default=0)
    q = s.add_parser('detail')
    q.add_argument('path')
    q.add_argument('--page', type=int, default=0)
    a = p.parse_args()
    print(json.dumps(farm_reclamation_list(a.keyword, a.page) if a.cmd == 'list' else farm_reclamation_detail(a.path, a.page), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
