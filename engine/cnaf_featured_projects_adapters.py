"""国家艺术基金官网资助成果展示目录。"""
import release_runtime
import re, subprocess
from html.parser import HTMLParser
from urllib.parse import urlencode, urljoin
ROOT = 'https://www.cnaf.cn'
CATEGORIES = {'大型舞台剧和作品创作': 14, '中小型剧目和作品创作': 15, '美术创作': 16, '传播交流推广': 17, '艺术人才培训': 18, '青年艺术创作人才': 19}

class _Cards(HTMLParser):

    def __init__(self):
        super().__init__()
        self.indiv = 0
        self.item_depth = None
        self.row = None
        self.active = []
        self.rows = []
        self.pages = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cs = a.get('class', '').split()
        if a.get('id') == 'btn_new' and a.get('data-max', '').isdigit():
            self.pages = int(a['data-max'])
        if tag == 'div':
            self.indiv += 1
            if 'item' in cs and self.row is None:
                self.row = {'title': '', 'organization': '', 'year': ''}
                self.item_depth = self.indiv
            if self.row is not None:
                for cls, key in [('t1', 'title'), ('t', 'organization'), ('li', 'year')]:
                    if cls in cs:
                        self.active.append((self.indiv, key))
        elif tag == 'a' and self.row is not None and ('url' not in self.row):
            self.row['url'] = urljoin(ROOT, a.get('href', ''))

    def handle_data(self, text):
        if self.row is not None and self.active:
            self.row[self.active[-1][1]] += text

    def handle_endtag(self, tag):
        if tag == 'div':
            while self.active and self.active[-1][0] == self.indiv:
                self.active.pop()
            if self.row is not None and self.indiv == self.item_depth:
                row = {k: v.strip() for k, v in self.row.items()}
                if row['title']:
                    self.rows.append(row)
                self.row = None
                self.item_depth = None
            self.indiv -= 1

def cnaf_featured_projects(category='传播交流推广', page=1, keyword=''):
    if category not in CATEGORIES:
        raise ValueError('不支持该资助成果分类')
    page = int(page)
    if not 1 <= page <= 500:
        raise ValueError('页码必须在 1—500')
    q = urlencode({'category_id': CATEGORIES[category], 'tpl_file': 'common/declare', 'pagesize': 12, 'p': page})
    url = ROOT + '/searchs/funding.html?' + q
    raw = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '25', '--max-redirs', '0', url], check=True, capture_output=True).stdout.decode('utf-8-sig')
    p = _Cards()
    p.feed(raw)
    if not p.rows:
        raise ValueError('此页无成果或网页结构已改变')
    needle = ''.join(keyword.split()).casefold()
    return {'category': category, 'page': page, 'pages': p.pages, 'items': [r for r in p.rows if needle in ''.join((''.join(str(v).split()) for v in r.values())).casefold()], 'source_url': url}
