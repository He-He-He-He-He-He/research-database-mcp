"""国家林草局年度发展报告目录，只读。"""
import release_runtime
import argparse, json, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
BASE = 'https://www.forestry.gov.cn'
INDEX = BASE + '/c/www/ndfzbg.jhtml'

def fetch(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True)
    if p.returncode:
        raise RuntimeError('上游请求失败（curl 状态 %d）' % p.returncode)
    return p.stdout.decode('utf-8')

class Catalog(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.item = None
        self.parts = []
        self.items = []

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'div':
            if self.depth:
                self.depth += 1
            elif a.get('class') == 'news_list':
                self.depth = 1
        if self.depth and t == 'a':
            h = a.get('href', '')
            u = urljoin(BASE, h)
            x = urlsplit(u)
            if x.scheme == 'https' and x.hostname == 'www.forestry.gov.cn' and h.startswith('/'):
                self.item = {'path': x.path, 'url': u}
                self.parts = []

    def handle_data(self, s):
        if self.item:
            self.parts.append(s)

    def handle_endtag(self, t):
        if t == 'a' and self.item:
            self.item['title'] = ' '.join(''.join(self.parts).split())
            self.items.append(self.item)
            self.item = None
        if t == 'div' and self.depth:
            self.depth -= 1

class Body(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.done = False
        self.parts = []

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'div':
            if self.depth and a.get('class') == 'fr':
                self.depth = 0
                self.done = True
            elif self.depth:
                self.depth += 1
            elif not self.done and a.get('id') == 'zoomit':
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

def forestry_reports(keyword=''):
    p = Catalog()
    p.feed(fetch(INDEX))
    if not p.items:
        raise ValueError('未识别年度报告列表')
    return {'source': '国家林业和草原局年度发展报告', 'source_url': INDEX, 'items': [x for x in p.items if keyword in x['title']], 'note': '筛选当前目录标题，包含 PDF，历史年份为主，不代表完整年鉴或所有资料。'}

def forestry_report_detail(path):
    matches = [x for x in forestry_reports()['items'] if x['path'] == path]
    if not matches:
        raise ValueError('路径不在当前官方目录')
    result = dict(matches[0])
    result['source'] = '国家林业和草原局年度发展报告'
    if path.lower().endswith('.pdf'):
        result['note'] = '官方 PDF 地址，未下载或提取内容。'
        return result
    parser = Body()
    parser.feed(fetch(result['url']))
    text = '\n'.join((x.strip() for x in ''.join(parser.parts).splitlines() if x.strip()))
    if not text:
        raise ValueError('未识别报告正文')
    result['text'] = text
    result['note'] = '只提取正文文字，图表与脚注请核对官方原文。'
    return result

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(forestry_reports(a.keyword) if a.cmd == 'list' else forestry_report_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
