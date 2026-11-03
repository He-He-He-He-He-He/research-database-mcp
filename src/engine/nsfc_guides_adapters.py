"""国家自然科学基金委员会项目指南通告，只读。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urljoin
BASE = 'https://www.nsfc.gov.cn/p1/3381/2824/'

def fetch(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True)
    if p.returncode:
        raise RuntimeError('上游请求失败（curl 状态 %d）' % p.returncode)
    return p.stdout.decode('utf-8')

class List(HTMLParser):

    def __init__(self):
        super().__init__()
        self.href = None
        self.text = []
        self.items = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        h = a.get('href', '')
        if tag == 'a' and re.fullmatch('/p1/3381/2824/\\d+\\.html', h):
            self.href = h
            self.text = []

    def handle_data(self, s):
        if self.href:
            self.text.append(s)

    def handle_endtag(self, tag):
        if tag == 'a' and self.href:
            self.items.append({'id': self.href.rsplit('/', 1)[-1][:-5], 'title': ' '.join(''.join(self.text).split()), 'url': urljoin(BASE, self.href)})
            self.href = None

class Detail(HTMLParser):

    def __init__(self):
        super().__init__()
        self.mode = None
        self.depth = 0
        self.parts = {'detail-title': [], 'detail-p': []}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if self.mode and tag == 'div':
            self.depth += 1
        elif not self.mode and tag == 'div' and (a.get('class') in self.parts):
            self.mode = a['class']
            self.depth = 1
        if self.mode and tag in ('p', 'br'):
            self.parts[self.mode].append('\n')

    def handle_data(self, s):
        if self.mode:
            self.parts[self.mode].append(s)

    def handle_endtag(self, tag):
        if self.mode and tag == 'div':
            self.depth -= 1
            if self.depth == 0:
                self.mode = None

def nsfc_guides(keyword='', page=1):
    if not isinstance(page, int) or not 1 <= page <= 1000:
        raise ValueError('页码应为 1 至 1000')
    url = BASE + ('zntg.html' if page == 1 else f'zntg_{page}.html')
    p = List()
    p.feed(fetch(url))
    if not p.items:
        raise ValueError('未识别项目指南列表；页码可能超出范围或页面已变化')
    return {'source': '国家自然科学基金委员会项目指南通告', 'source_url': url, 'page': page, 'items': [i for i in p.items if keyword in i['title']], 'note': '仅筛选指定列表页标题，列表标题可能被网站截断；详情可能要求登录基金系统查看完整指南。'}

def nsfc_guide_detail(identifier):
    if not re.fullmatch('\\d+', str(identifier)):
        raise ValueError('通告编号应为数字')
    url = BASE + str(identifier) + '.html'
    p = Detail()
    p.feed(fetch(url))
    title = ' '.join(''.join(p.parts['detail-title']).split())
    body = '\n'.join((x.strip() for x in ''.join(p.parts['detail-p']).splitlines() if x.strip()))
    if not title or not body:
        raise ValueError('未识别通告正文')
    return {'source': '国家自然科学基金委员会项目指南通告', 'url': url, 'id': str(identifier), 'title': title, 'text': body, 'note': '正文中提及的登录页面及附件须自行按官方要求访问，未绕过认证。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q.add_argument('--page', type=int, default=1)
    q = s.add_parser('detail')
    q.add_argument('id')
    a = p.parse_args()
    print(json.dumps(nsfc_guides(a.keyword, a.page) if a.cmd == 'list' else nsfc_guide_detail(a.id), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
