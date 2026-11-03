"""Global Science Press 网站公开期刊目录，非浙大订购清单。"""
import release_runtime
import argparse, json, subprocess
from html.parser import HTMLParser
from urllib.parse import urljoin
URL = 'https://www.global-sci.com/index/site_page/journals'

class Parser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.items = []
        self.row = None
        self.depth = 0
        self.field = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get('class', '').split()
        if self.row is None and tag == 'div' and ('jlp-row' in cls) and ('jlp-row--head' not in cls):
            self.row = {'title': '', 'url': '', 'abbreviation': '', 'editors': '', 'indexing': ''}
            self.depth = 1
            return
        if self.row is None:
            return
        if tag == 'div':
            self.depth += 1
        fields = {'jlp-row__title': 'title', 'jlp-row__acro': 'abbreviation', 'jlp-row__eic': 'editors', 'jlp-row__indexed': 'indexing'}
        for c, f in fields.items():
            if c in cls:
                self.field = (tag, f)
                if f == 'title':
                    self.row['url'] = urljoin(URL, a.get('href', ''))

    def handle_data(self, data):
        if self.row and self.field:
            self.row[self.field[1]] += data

    def handle_endtag(self, tag):
        if self.row is None:
            return
        if self.field and self.field[0] == tag:
            self.field = None
        if tag == 'div':
            self.depth -= 1
            if self.depth == 0:
                for k in self.row:
                    self.row[k] = ' '.join(self.row[k].split())
                if self.row['title'] and self.row['url']:
                    self.items.append(self.row)
                self.row = None

def search(keyword=''):
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '30', URL], capture_output=True, text=True, timeout=35)
    if p.returncode:
        raise RuntimeError('期刊目录请求失败: ' + p.stderr.strip())
    parser = Parser()
    parser.feed(p.stdout)
    if not parser.items:
        raise RuntimeError('未识别期刊目录，网站结构可能已变化')
    q = keyword.casefold()
    items = [x for x in parser.items if q in ' '.join(x.values()).casefold()]
    return {'source': 'Global Science Press 公开期刊目录', 'scope': '网站全平台公开期刊清单；不是浙江大学订购清单，不证明机构授权或全文可用', 'keyword': keyword, 'total_catalog': len(parser.items), 'total': len(items), 'items': items}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('keyword', nargs='?', default='')
    a = p.parse_args()
    print(json.dumps(search(a.keyword), ensure_ascii=False, indent=2))
