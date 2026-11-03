"""上海市行政规范性文件数据库公开目录检索。"""
import release_runtime
import json, re, subprocess
from html.parser import HTMLParser
from urllib.parse import urlencode, urljoin
BASE = 'https://service.shanghai.gov.cn/xingzhengwendangkujyh/'

class Parser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.table = False
        self.table_seen = False
        self.row = None
        self.cell = None
        self.items = []
        self.page = None
        self.bad = 0

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'table' and 'table-list' in a.get('class', '').split():
            self.table = True
            self.table_seen = True
        elif self.table and t == 'tr':
            self.row = {'cells': [], 'title': '', 'url': ''}
        elif self.table and self.row is not None and (t == 'td'):
            self.cell = []
        elif self.table and self.row is not None and (t == 'a'):
            href = a.get('href', '')
            if re.fullmatch('XZGFDetails\\.aspx\\?docid=[A-Za-z0-9]+', href) and a.get('title'):
                self.row['title'] = a['title']
                self.row['url'] = urljoin(BASE, href)
            else:
                self.bad += 1
        elif t == 'control_page':
            self.page = a

    def handle_data(self, s):
        if self.cell is not None:
            self.cell.append(s)

    def handle_endtag(self, t):
        if t == 'td' and self.row is not None and (self.cell is not None):
            self.row['cells'].append(' '.join(''.join(self.cell).split()))
            self.cell = None
        if t == 'tr' and self.row is not None:
            if self.row['url'] and len(self.row['cells']) >= 3:
                self.items.append({'title': self.row['title'], 'number': self.row['cells'][1], 'effective_date': self.row['cells'][2], 'url': self.row['url']})
            elif self.row['cells']:
                self.bad += 1
            self.row = None
        if t == 'table' and self.table:
            self.table = False

def search(keyword='', page=1, number=''):
    if not 1 <= int(page) <= 10000:
        raise ValueError('页码须为正整数')
    url = BASE + 'XZGFList.aspx?' + urlencode({'kw': keyword, 'wenhao': number, 'currentPage': int(page), 'pagesize': 10})
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '25', url], capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError('上海文件库请求失败: ' + p.stderr.strip())
    parser = Parser()
    parser.feed(p.stdout)
    try:
        if not parser.table_seen or parser.bad or parser.page is None:
            raise ValueError('结果表不完整')
        total = int(parser.page['count'])
        current = int(parser.page['page'])
        size = int(parser.page['pagesize'])
        if current != int(page) or size != 10:
            raise ValueError('实际页码或数量不符')
        if total > 0 and (not parser.items) and ((current - 1) * size < total):
            raise ValueError('结果页为空但总数显示有记录')
    except (ValueError, KeyError, TypeError) as exc:
        raise RuntimeError('上海文件库响应异常，未返回部分题录') from exc
    return {'source': '上海市行政规范性文件数据库', 'keyword': keyword, 'page': current, 'page_size': size, 'total': total, 'items': parser.items, 'scope': '官网默认筛选范围下公开文件目录；状态、现行效力及正文以官网详情和后续文件核验为准'}
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('keyword', nargs='?', default='')
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--number', default='')
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.page, a.number), ensure_ascii=False, indent=2))
