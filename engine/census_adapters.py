"""国家统计局全国人口普查公报目录和正文，只读。"""
import release_runtime
import argparse, json, re, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from research import fetch
BASE = 'https://www.stats.gov.cn/sj/tjgb/rkpcgb/qgrkpcgb/'

class Listing(HTMLParser):

    def __init__(self):
        super().__init__()
        self.items = {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        h = a.get('href', '')
        title = a.get('title', '')
        if tag == 'a' and re.fullmatch('\\./\\d{6}/t\\d{8}_\\d+\\.html', h) and ('人口普查公报' in title):
            self.items[urljoin(BASE, h)] = {'title': title, 'url': urljoin(BASE, h)}

class Article(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.found = False
        self.text = []
        self.table = None
        self.row = None
        self.cell = None
        self.tables = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if not self.depth and tag == 'div' and ('txt-content' in a.get('class', '').split()):
            self.depth = 1
            self.found = True
            return
        if not self.depth:
            return
        if tag == 'div':
            self.depth += 1
        if tag in ('p', 'br'):
            self.text.append('\n')
        if tag == 'table':
            self.table = []
        if tag == 'tr' and self.table is not None:
            self.row = []
        if tag in ('td', 'th') and self.row is not None:
            self.cell = {'text': '', 'rowspan': a.get('rowspan', '1'), 'colspan': a.get('colspan', '1')}

    def handle_data(self, s):
        if self.depth:
            self.text.append(s)
        if self.cell is not None:
            self.cell['text'] += s

    def handle_endtag(self, tag):
        if not self.depth:
            return
        if tag in ('td', 'th') and self.cell is not None:
            self.cell['text'] = ' '.join(self.cell['text'].split())
            self.row.append(self.cell)
            self.cell = None
        if tag == 'tr' and self.row is not None:
            self.table.append(self.row)
            self.row = None
        if tag == 'table' and self.table is not None:
            self.tables.append(self.table)
            self.table = None
        if tag == 'div':
            self.depth -= 1

def census_list(keyword=''):
    p = Listing()
    p.feed(fetch(BASE))
    if not p.items:
        raise ValueError('未识别普查公报目录')
    return {'source': '国家统计局', 'source_url': BASE, 'scope': '全国人口普查公报当前目录页', 'items': [x for x in p.items.values() if keyword in x['title']], 'note': '只筛当前页面标题，普查时点与统计口径以公报为准。'}

def census_list_all(keyword=''):
    if not isinstance(keyword, str):
        raise ValueError('关键词须为字符串')

    def page(n):
        url = BASE if n == 1 else BASE + f'index_{n - 1}.html'
        html = fetch(url)
        m = re.search('createPageHTML\\(\\s*(\\d+)\\s*,\\s*(\\d+)\\s*,\\s*["\\\']index["\\\']\\s*,\\s*["\\\']html["\\\']\\s*\\)', html)
        if not m or int(m.group(2)) != n - 1:
            raise ValueError('来源页码或分页信息无法核验')
        p = Listing()
        p.feed(html)
        if not p.items:
            raise ValueError('未识别普查公报目录')
        return (url, int(m.group(1)), list(p.items.values()))
    u, pages, first = page(1)
    if not 1 <= pages <= 20:
        raise ValueError('目录页数超过本次遍历上限')
    rows = []
    seen = set()
    sources = []
    for n in range(1, pages + 1):
        url, p, items = (u, pages, first) if n == 1 else page(n)
        if p != pages:
            raise ValueError('目录总页数变化，请重新查询')
        sources.append(url)
        for item in items:
            if item['url'] in seen:
                raise ValueError('跨页出现重复链接，目录可能更新')
            seen.add(item['url'])
            rows.append(item)
    matches = [x for x in rows if keyword in x['title']]
    return {'source': '国家统计局全国人口普查公报目录', 'keyword': keyword, 'source_pages': pages, 'source_urls': sources, 'parsed_items': len(rows), 'matched_count': len(matches), 'items': matches, 'note': '逐页筛选当前栏目标题；来源未提供条目总数，跨页非原子快照，不代表全部历次普查材料。具体时点、口径和注释须核公报。'}

def census_detail(url):
    x = urlsplit(url)
    if x.scheme != 'https' or x.netloc != 'www.stats.gov.cn' or x.query or x.fragment or (not re.fullmatch('/sj/tjgb/rkpcgb/qgrkpcgb/\\d{6}/t\\d{8}_\\d+\\.html', x.path)):
        raise ValueError('只接受本目录的国家统计局公报地址')
    p = Article()
    p.feed(fetch(url))
    if not p.found:
        raise ValueError('未识别公报正文')
    return {'source_url': url, 'text': ''.join(p.text).strip(), 'tables': p.tables, 'note': '保留单元格合并标记，图像表格未解析；核对原文注释和普查范围。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('list-all')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('url')
    a = p.parse_args()
    print(json.dumps(census_list(a.keyword) if a.cmd == 'list' else census_list_all(a.keyword) if a.cmd == 'list-all' else census_detail(a.url), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或页面结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
