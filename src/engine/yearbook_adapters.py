"""国家统计局中国统计年鉴2025目录与说明，只读。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urljoin
BASE = 'https://www.stats.gov.cn/sj/ndsj/2025/'

def gb_fetch(url):
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True)
    if r.returncode:
        raise RuntimeError('上游查询失败（curl 状态 %d）' % r.returncode)
    return r.stdout.decode('gb18030')

class Index(HTMLParser):

    def __init__(self):
        super().__init__()
        self.href = None
        self.parts = []
        self.items = {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        u = a.get('href', '')
        if tag == 'a' and re.fullmatch('html/[A-Za-z0-9_-]+\\.(?:htm|jpg|pdf)', u, re.I):
            self.href = u
            self.parts = []

    def handle_data(self, s):
        if self.href:
            self.parts.append(s)

    def handle_endtag(self, tag):
        if tag == 'a' and self.href:
            title = ' '.join(''.join(self.parts).split())
            if title:
                self.items[self.href] = {'title': title, 'path': self.href, 'url': urljoin(BASE, self.href), 'format': self.href.rsplit('.', 1)[-1].lower()}
            self.href = None

class Body(HTMLParser):

    def __init__(self):
        super().__init__()
        self.in_body = False
        self.text = []

    def handle_starttag(self, tag, attrs):
        if tag == 'body':
            self.in_body = True
        if self.in_body and tag in ('p', 'br'):
            self.text.append('\n')

    def handle_data(self, s):
        if self.in_body:
            self.text.append(s)

    def handle_endtag(self, tag):
        if tag == 'body':
            self.in_body = False

def yearbook_list(keyword=''):
    p = Index()
    p.feed(gb_fetch(BASE + 'left.htm'))
    if not p.items:
        raise ValueError('未识别统计年鉴目录')
    return {'source': '中国统计年鉴2025', 'source_url': BASE + 'indexch.htm', 'catalog_total': len(p.items), 'items': [x for x in p.items.values() if keyword in x['title']], 'note': '目录按标题筛选；表格多为图片，不提供结构化数值。'}

def yearbook_detail(path):
    if not re.fullmatch('html/[A-Za-z0-9_-]+\\.(?:htm|jpg|pdf)', path, re.I):
        raise ValueError('年鉴路径格式不正确')
    items = yearbook_list()['items']
    match = [x for x in items if x['path'] == path]
    if not match:
        raise ValueError('路径不在当前年鉴目录')
    out = dict(match[0])
    out['source'] = '中国统计年鉴2025'
    out['note'] = '原表为图片或 PDF 时只返回官方地址，未解析数值；统计口径请核对章节说明。'
    if out['format'] == 'htm':
        p = Body()
        p.feed(gb_fetch(out['url']))
        out['text'] = ''.join(p.text).strip()
    return out

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(yearbook_list(a.keyword) if a.cmd == 'list' else yearbook_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
