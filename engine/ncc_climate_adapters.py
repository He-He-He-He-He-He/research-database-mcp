"""国家气候中心中国气候公报目录与已核实的报告简介。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urlsplit
BASE = 'https://www.ncc-cma.net'
INDEX = BASE + '/channel/index/wid/203'
VERIFIED = {'100932', '100659'}

def fetch(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True)
    if p.returncode:
        raise RuntimeError('上游请求失败（curl 状态 %d）' % p.returncode)
    return p.stdout.decode('utf-8')

class Catalog(HTMLParser):

    def __init__(self):
        super().__init__()
        self.id = None
        self.capture = False
        self.parts = []
        self.items = {}

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        x = urlsplit(a.get('href', ''))
        m = re.fullmatch('/channel/news/newsid/(\\d+)', x.path)
        if t == 'a' and x.hostname == 'www.ncc-cma.net' and m:
            self.id = m.group(1)
        if self.id and t == 'div' and ('news-nav-title' in a.get('class', '').split()):
            self.capture = True
            self.parts = []

    def handle_data(self, s):
        if self.capture:
            self.parts.append(s)

    def handle_endtag(self, t):
        if t == 'div' and self.capture:
            self.items[self.id] = {'id': self.id, 'title': ' '.join(''.join(self.parts).split()), 'list_link': BASE + '/channel/news/newsid/' + self.id, 'overview_url': BASE + '/channel/research/researchid/' + self.id if self.id in VERIFIED else None}
            self.capture = False
        if t == 'a':
            self.id = None

class Body(HTMLParser):

    def __init__(self):
        super().__init__()
        self.active = None
        self.parts = {'research-title': [], 'research-intro': []}

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'div' and a.get('class') in self.parts:
            self.active = a['class']

    def handle_data(self, s):
        if self.active:
            self.parts[self.active].append(s)

    def handle_endtag(self, t):
        if t == 'div' and self.active:
            self.active = None

def ncc_climate_reports(keyword=''):
    p = Catalog()
    p.feed(fetch(INDEX))
    if not p.items:
        raise ValueError('未识别气候公报目录')
    return {'source': '中国气象局国家气候中心中国气候公报', 'source_url': INDEX, 'items': [i for i in p.items.values() if keyword in i['title']], 'note': '目录原详情链接本次返回提示页；仅为已核验的 2024、2025 年提供独立公开简介链接，未提供完整公报数据。'}

def ncc_climate_detail(identifier):
    if identifier not in VERIFIED:
        raise ValueError('仅支持已核验的 2024、2025 年简介编号')
    matches = [i for i in ncc_climate_reports()['items'] if i['id'] == identifier]
    if not matches:
        raise ValueError('编号不在当前目录')
    url = matches[0]['overview_url']
    p = Body()
    p.feed(fetch(url))
    title = ''.join(p.parts['research-title']).strip()
    text = ''.join(p.parts['research-intro']).strip()
    if not title or not text:
        raise ValueError('未识别简介')
    return {'source': '中国气象局国家气候中心中国气候公报', 'id': identifier, 'title': title, 'url': url, 'text': text, 'note': '仅公报简介，不是全文、图表或观测数据。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('id')
    a = p.parse_args()
    print(json.dumps(ncc_climate_reports(a.keyword) if a.cmd == 'list' else ncc_climate_detail(a.id), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
