"""国家能源局发展规划司公开工作进展目录与正文。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
BASE = 'https://www.nea.gov.cn/sjzz/ghs/'
INDEX = BASE + 'ds_99a01b29f9a24ab58f7d64b36489500e.json'

def fetch(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True)
    if p.returncode:
        raise RuntimeError('上游请求失败（curl 状态 %d）' % p.returncode)
    return p.stdout.decode('utf-8')

def nea_progress(keyword=''):
    data = json.loads(fetch(INDEX))
    rows = data.get('datasource')
    if not isinstance(rows, list):
        raise ValueError('未识别工作进展目录')
    items = []
    for r in rows:
        title = r.get('showTitle') or r.get('title') or ''
        url = urljoin(BASE, r.get('publishUrl') or '')
        x = urlsplit(url)
        if keyword in title and x.scheme == 'https' and (x.hostname == 'www.nea.gov.cn') and re.fullmatch('/\\d{8}/[0-9a-f]{32}/c\\.html', x.path):
            items.append({'title': title, 'url': url, 'path': x.path, 'published': r.get('publishTime')})
    return {'source': '国家能源局发展规划司工作进展', 'source_url': BASE + 'index.htm', 'keyword': keyword, 'items': items, 'note': '仅筛选该司当前工作进展目录标题，不是能源全站检索；未解析图片中的表格。'}

class Body(HTMLParser):

    def __init__(self):
        super().__init__()
        self.active = False
        self.parts = []
        self.images = []
        self.meta = {}

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'meta' and a.get('name') in ('ArticleTitle', 'PubDate'):
            self.meta[a['name']] = a.get('content', '')
        if t == 'span' and a.get('id') == 'detailContent':
            self.active = True
        elif self.active:
            if t in ('p', 'br', 'tr'):
                self.parts.append('\n')
            if t == 'img' and a.get('src'):
                self.images.append(a['src'])

    def handle_data(self, s):
        if self.active:
            self.parts.append(s)

    def handle_endtag(self, t):
        if self.active and t == 'span':
            self.active = False

def nea_progress_detail(path):
    if not re.fullmatch('/\\d{8}/[0-9a-f]{32}/c\\.html', path):
        raise ValueError('路径格式错误')
    matches = [x for x in nea_progress()['items'] if x['path'] == path]
    if not matches:
        raise ValueError('路径不在当前工作进展目录')
    url = matches[0]['url']
    p = Body()
    p.feed(fetch(url))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if not p.meta.get('ArticleTitle') or not text:
        raise ValueError('未识别正文')
    images = []
    for i in p.images:
        u = urljoin(url, i)
        x = urlsplit(u)
        if x.scheme == 'https' and x.hostname == 'www.nea.gov.cn':
            images.append(u)
    return {'source': '国家能源局发展规划司工作进展', 'url': url, 'title': p.meta['ArticleTitle'], 'published': p.meta.get('PubDate'), 'text': text, 'images': images, 'note': '图片表格只返回链接，未解析；请核对官方口径及图表。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(nea_progress(a.keyword) if a.cmd == 'list' else nea_progress_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
