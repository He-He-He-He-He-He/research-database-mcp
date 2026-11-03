"""公安标准化信息服务平台公开标准查询。"""
import release_runtime
import argparse, json, re, sys
from html.parser import HTMLParser
from urllib.parse import urlencode, urljoin
from research import fetch
BASE = 'https://ywtb.mps.gov.cn'
SEARCH = BASE + '/gabzh/portal/xxcx/std'

class Table(HTMLParser):

    def __init__(self):
        super().__init__()
        self.table = False
        self.seen = False
        self.row = None
        self.cell = None
        self.rows = []
        self.url = ''

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'table' and 'table-bordered' in a.get('class', '').split():
            self.table = True
            self.seen = True
        if self.table and t == 'tr':
            self.row = []
            self.url = ''
        if self.table and self.row is not None and (t == 'td'):
            self.cell = ''
        if self.table and t == 'a' and re.fullmatch('/gabzh/portal/stdDetail/-?\\d+', a.get('href', '')):
            self.url = urljoin(BASE, a['href'])

    def handle_data(self, d):
        if self.cell is not None:
            self.cell += d

    def handle_endtag(self, t):
        if t == 'td' and self.cell is not None:
            self.row.append(' '.join(self.cell.split()))
            self.cell = None
        if t == 'tr' and self.row is not None:
            if len(self.row) == 6 and self.url:
                self.rows.append(dict(zip(['index', 'number', 'title', 'published', 'effective', 'status', 'url'], self.row + [self.url])))
            self.row = None
        if t == 'table' and self.table:
            self.table = False

class Detail(HTMLParser):

    def __init__(self):
        super().__init__()
        self.tag = ''
        self.text = ''
        self.label = None
        self.fields = {}
        self.status = ''
        self.in_status = False

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t in ('dt', 'dd') and 'basicInfo-item' in a.get('class', '').split():
            self.tag = t
            self.text = ''
        if t == 'span' and 's-status' in a.get('class', '').split():
            self.in_status = True

    def handle_data(self, d):
        if self.tag:
            self.text += d
        if self.in_status:
            self.status += d

    def handle_endtag(self, t):
        if t == 'span':
            self.in_status = False
        if t == self.tag:
            value = ' '.join(self.text.split())
            if t == 'dt':
                self.label = value
            elif self.label:
                self.fields[self.label] = value
                self.label = None
            self.tag = ''
            self.text = ''

def search(keyword='', page=1, size=20, status='', level=''):
    if not 1 <= page <= 10000 or not 1 <= size <= 50 or status not in ('', '现行', '废止', '即将实施') or (level not in ('', 'GB', 'HB')):
        raise ValueError('查询条件无效')
    params = {'pageNo': page, 'pageSize': size}
    if keyword:
        params['key'] = keyword
    if status:
        params['repeFlag'] = status
    if level:
        params['level'] = level
    url = SEARCH + '?' + urlencode(params)
    html = fetch(url)
    p = Table()
    p.feed(html)
    if not p.seen:
        raise ValueError('未找到查询表格，上游可能改版或要求验证')
    m = re.search("pages:parseInt\\('([0-9]+)'\\)", html)
    return {'source': url, 'page': page, 'pages': int(m.group(1)) if m else None, 'items': p.rows, 'note': '标准题录和状态由上游提供；全文和后续变更以官方为准。'}

def detail(id):
    if not re.fullmatch('-?\\d{1,12}', str(id)):
        raise ValueError('ID须为数字')
    url = BASE + '/gabzh/portal/stdDetail/' + str(id)
    p = Detail()
    p.feed(fetch(url))
    if not p.fields:
        raise ValueError('未找到标准基础信息')
    status = next((x for x in ('即将实施', '现行', '废止') if x in p.status), None)
    return {'source': url, 'status': status, 'fields': p.fields}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('search')
    q.add_argument('keyword', nargs='?', default='')
    q.add_argument('--page', type=int, default=1)
    q.add_argument('--size', type=int, default=20)
    q.add_argument('--status', choices=['现行', '废止', '即将实施'], default='')
    q.add_argument('--level', choices=['GB', 'HB'], default='')
    q = s.add_parser('detail')
    q.add_argument('id')
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.page, a.size, a.status, a.level) if a.cmd == 'search' else detail(a.id), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
