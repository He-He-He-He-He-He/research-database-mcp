"""国家新闻出版署统计信息目录及公开 PDF 文本，只读。"""
import release_runtime
import argparse, io, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urljoin
BASE = 'https://www.nppa.gov.cn/xxgk/fdzdgknr/tjxx/'

def fetch(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True)
    if p.returncode:
        raise RuntimeError('上游请求失败（curl 状态 %d）' % p.returncode)
    return p.stdout

class Catalog(HTMLParser):

    def __init__(self):
        super().__init__()
        self.href = None
        self.parts = []
        self.items = []

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        h = a.get('href', '')
        if t == 'a' and re.fullmatch('\\./\\d{6}/P\\d+\\.pdf', h):
            self.href = h[2:]
            self.parts = []

    def handle_data(self, s):
        if self.href:
            self.parts.append(s)

    def handle_endtag(self, t):
        if t == 'a' and self.href:
            title = ' '.join(''.join(self.parts).split())
            if title:
                self.items.append({'title': title, 'path': self.href, 'url': urljoin(BASE, self.href)})
            self.href = None

def nppa_statistics(keyword=''):
    p = Catalog()
    p.feed(fetch(BASE).decode('utf-8'))
    if not p.items:
        raise ValueError('未识别新闻出版统计目录')
    return {'source': '国家新闻出版署统计信息', 'source_url': BASE, 'items': [i for i in p.items if keyword in i['title']], 'note': '仅当前栏目列出的统计公报和报告 PDF 标题筛选，不含全站。'}

def nppa_statistic_detail(path):
    matches = [i for i in nppa_statistics()['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在当前目录')
    try:
        from pypdf import PdfReader
    except ImportError:
        raise RuntimeError('读取 PDF 需要安装 pypdf；也可打开目录返回的官方链接')
    raw = fetch(matches[0]['url'])
    if not raw.startswith(b'%PDF-'):
        raise ValueError('上游未返回 PDF')
    reader = PdfReader(io.BytesIO(raw))
    pages = [page.extract_text() or '' for page in reader.pages]
    if not any((x.strip() for x in pages)):
        raise ValueError('PDF 未提取到文字，可能是扫描版')
    return {'source': '国家新闻出版署统计信息', **matches[0], 'page_count': len(pages), 'pages': pages, 'note': 'PDF 文字按页提取；表格、脚注和字符可能错位，不执行 OCR，请核对原文。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(nppa_statistics(a.keyword) if a.cmd == 'list' else nppa_statistic_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
