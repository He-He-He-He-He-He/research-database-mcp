"""国家统计局信息公开统计公报目录。"""
import release_runtime
import argparse, json, re, sys
from html.parser import HTMLParser
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from stats_release_adapters import Body, fetch
BASE = 'https://www.stats.gov.cn/xxgk/sjfb/tjgb2020/'

class Catalog(HTMLParser):

    def __init__(self):
        super().__init__()
        self.path = None
        self.parts = []
        self.items = {}

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        h = a.get('href', '')
        if t == 'a' and re.fullmatch('\\./\\d{6}/t\\d{8}_\\d+\\.html', h):
            self.path = h[2:]
            self.parts = []

    def handle_data(self, s):
        if self.path:
            self.parts.append(s)

    def handle_endtag(self, t):
        if t == 'a' and self.path:
            title = ' '.join(''.join(self.parts).split())
            if title:
                self.items[self.path] = {'path': self.path, 'title': title, 'url': urljoin(BASE, self.path)}
            self.path = None

def national_bulletins(keyword=''):
    p = Catalog()
    p.feed(fetch(BASE))
    if not p.items:
        raise ValueError('未识别统计公报目录')
    return {'source': '国家统计局信息公开统计公报', 'source_url': BASE, 'items': [i for i in p.items.values() if keyword in i['title']], 'note': '仅当前目录首页标题筛选，不是国家数据指标库或全部历史。'}

def national_bulletin_detail(path):
    matches = [i for i in national_bulletins()['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在当前目录')
    html = fetch(matches[0]['url'])
    p = Body()
    p.feed(html)
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if not p.title or not text:
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.select_one('h2.xxgkNbXqTitle')
        body = soup.select_one('div.TRS_Editor') or soup.select_one('div.xxgkNbXqCenter > div.TRS_PreAppend')
        if not title or not body or title.get_text(' ', strip=True) != matches[0]['title']:
            raise ValueError('未识别统计公报正文')
        p.title = title.get_text(' ', strip=True)
        text = body.get_text('\n', strip=True)
        if len(text) < 500:
            raise ValueError('统计公报正文过短，可能访问受限')
        p.rows = [[cell.get_text(' ', strip=True) for cell in row.find_all(['td', 'th'], recursive=False)] for table in body.find_all('table') for row in table.find_all('tr')]
    return {'source': '国家统计局信息公开统计公报', 'title': p.title, 'url': matches[0]['url'], 'text': text, 'table_rows': p.rows, 'note': '仅 HTML 原始表格行，未重建合并单元格或解析图片；数值及附注请核对原文。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(national_bulletins(a.keyword) if a.cmd == 'list' else national_bulletin_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
