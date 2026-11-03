"""全国社会保障基金理事会全国社保基金年度报告。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
BASE = 'https://www.ssf.gov.cn'
INDEX = BASE + '/portal/xxgk/fdzdgknr/cwbg/sbjjndbg/A0010030801index_1.htm'

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
        if t == 'a' and title and re.fullmatch('/portal/xxgk/fdzdgknr/cwbg/sbjjndbg/webinfo/\\d{4}/\\d{2}/\\d+\\.htm', h):
            self.items[h] = {'path': h, 'title': title, 'url': BASE + h}

class Body(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.parts = []
        self.title = ''

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'meta' and a.get('name') == 'ArticleTitle':
            self.title = a.get('content', '')
        if t == 'div':
            if self.depth:
                self.depth += 1
            elif a.get('id') == 'BodyLabel':
                self.depth = 1
        if self.depth and t in ('p', 'br', 'tr'):
            self.parts.append('\n')
        if self.depth and t in ('td', 'th'):
            self.parts.append('\t')

    def handle_data(self, s):
        if self.depth:
            self.parts.append(s)

    def handle_endtag(self, t):
        if t == 'div' and self.depth:
            self.depth -= 1

def ssf_reports(keyword=''):
    p = Catalog()
    p.feed(fetch(INDEX))
    if not p.items:
        raise ValueError('未识别社保基金报告目录')
    return {'source': '全国社会保障基金理事会全国社保基金年度报告', 'source_url': INDEX, 'items': [i for i in p.items.values() if keyword in i['title']], 'note': '仅本目录首页，报告是全国社会保障基金战略储备基金，不是个人社保账户或基本养老保险受托运营报告。'}

def ssf_report_detail(path):
    matches = [i for i in ssf_reports()['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在当前目录首页')
    p = Body()
    p.feed(fetch(matches[0]['url']))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if not p.title or not text:
        raise ValueError('未识别年报正文')
    return {'source': '全国社会保障基金理事会全国社保基金年度报告', 'title': p.title, 'url': matches[0]['url'], 'text': text, 'note': '仅提取网页文字；表格行列及财务附注须核对官方原文及审计报告。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(ssf_reports(a.keyword) if a.cmd == 'list' else ssf_report_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
