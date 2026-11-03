"""国家广播电视总局公告公示栏目，只读。"""
import release_runtime
import argparse, html, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
BASE = 'https://www.nrta.gov.cn'
INDEX = BASE + '/col/col113/index.html'

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
        self.links = []

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'meta' and a.get('name') == 'ArticleTitle':
            self.title = a.get('content', '')
        if t == 'div':
            if self.depth:
                self.depth += 1
            elif a.get('id') == 'zoom':
                self.depth = 1
        if self.depth and t in ('p', 'br', 'div', 'tr'):
            self.parts.append('\n')
        if self.depth and t in ('td', 'th'):
            self.parts.append('\t')
        if self.depth and t == 'a' and a.get('href'):
            self.links.append(a['href'])

    def handle_data(self, s):
        if self.depth:
            self.parts.append(s)

    def handle_endtag(self, t):
        if self.depth and t == 'div':
            self.depth -= 1

def nrta_announcements(keyword=''):
    text = fetch(INDEX)
    pairs = re.findall('<a\\s+href="(https://www\\.nrta\\.gov\\.cn/art/\\d{4}/\\d{1,2}/\\d{1,2}/art_113_\\d+\\.html)"\\s+title="([^"]+)"', text)
    if not pairs:
        raise ValueError('未识别公告目录')
    items = []
    seen = set()
    for url, title in pairs:
        title = html.unescape(title)
        if url not in seen and keyword in title:
            items.append({'title': title, 'url': url, 'path': urlsplit(url).path})
            seen.add(url)
    return {'source': '国家广播电视总局公告公示', 'source_url': INDEX, 'items': items, 'note': '只筛选栏目首页内嵌的公开公告条目，不代表全站或全部历史结果。'}

def nrta_announcement_detail(path):
    matches = [i for i in nrta_announcements()['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在当前栏目条目')
    url = matches[0]['url']
    p = Body()
    p.feed(fetch(url))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if not p.title or not text:
        raise ValueError('未识别公告正文')
    links = []
    for link in p.links:
        u = urljoin(url, link)
        x = urlsplit(u)
        if x.scheme == 'https' and x.hostname == 'www.nrta.gov.cn' and x.path.lower().endswith(('.pdf', '.xls', '.xlsx', '.doc', '.docx')):
            links.append(u)
    return {'source': '国家广播电视总局公告公示', 'title': p.title, 'url': url, 'text': text, 'attachments': links, 'note': '只返回正文文字和附件链接，不自动解析附件或图表，内容以官方原文为准。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(nrta_announcements(a.keyword) if a.cmd == 'list' else nrta_announcement_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
