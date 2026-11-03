"""中央国家机关住房资金管理中心公开北京住房公积金年度报告。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
BASE = 'https://www.zzz.gov.cn'
INDEX = BASE + '/html/xxgk/gjjndbg/'

def fetch(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True)
    if p.returncode:
        raise RuntimeError('上游请求失败（curl 状态 %d）' % p.returncode)
    return p.stdout.decode('utf-8', errors='replace')

class Catalog(HTMLParser):

    def __init__(self):
        super().__init__()
        self.href = None
        self.parts = []
        self.items = []

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        h = a.get('href', '')
        if t == 'a' and re.fullmatch('/html/xxgk/gjjndbg/\\d+\\.html', h):
            self.href = h
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
        self.parts = []

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'div':
            if self.depth:
                self.depth += 1
            elif 'paragraph' in a.get('class', '').split():
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

def housing_fund_reports(keyword=''):
    p = Catalog()
    p.feed(fetch(INDEX))
    if not p.items:
        raise ValueError('未识别住房公积金报告目录')
    return {'source': '中央国家机关住房资金管理中心住房公积金年度报告', 'source_url': INDEX, 'items': [i for i in p.items if keyword in i['title']], 'note': '仅筛选当前目录首页标题，报告为北京住房公积金年度报告，不是全国数据或个人账户数据。'}

def housing_fund_detail(path):
    matches = [i for i in housing_fund_reports()['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在当前目录首页')
    p = Body()
    p.feed(fetch(matches[0]['url']))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if not text:
        raise ValueError('未识别报告正文')
    return {'source': '中央国家机关住房资金管理中心住房公积金年度报告', 'title': matches[0]['title'], 'url': matches[0]['url'], 'text': text, 'note': '仅正文文字；统计口径、表格与图表请核对原文。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(housing_fund_reports(a.keyword) if a.cmd == 'list' else housing_fund_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
