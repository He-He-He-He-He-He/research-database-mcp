"""CIDP 制造业数字资源平台公开结果页题录检索。"""
import release_runtime
from html.parser import HTMLParser
import re, subprocess
from urllib.parse import urlencode, urljoin
BASE = 'https://www.cidp.com.cn'

class Parser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.table = False
        self.table_seen = False
        self.row = None
        self.cell = None
        self.items = []
        self.bad_rows = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'table' and a.get('id') == 'resultTab':
            self.table = True
            self.table_seen = True
        if self.table and tag == 'tr':
            m = re.fullmatch("window\\.open\\('(/web/[A-Za-z]+/[A-Za-z0-9]+)'\\)", a.get('onclick', ''))
            if a.get('onclick') and (not m):
                self.bad_rows += 1
            self.row = {'url': urljoin(BASE, m.group(1)), 'title': '', 'author': '', 'date': ''} if m else None
        if self.row is not None and tag == 'td':
            if a.get('title'):
                self.row['title'] = a['title']
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if self.row is not None and tag == 'td' and (self.cell is not None):
            val = ' '.join(''.join(self.cell).split())
            self.row.setdefault('_cells', []).append(val)
            self.cell = None
        if tag == 'tr' and self.row is not None:
            cells = self.row.pop('_cells', [])
            if self.row['title']:
                if len(cells) >= 3:
                    self.row['author'], self.row['date'] = cells[1:3]
                self.items.append(self.row)
            else:
                self.bad_rows += 1
            self.row = None
        if tag == 'table' and self.table:
            self.table = False

def search(keyword, page=1, resource_type='all'):
    if not keyword.strip() or not 1 <= int(page) <= 10000:
        raise ValueError('请输入关键词，页码须为正整数')
    types = {'all': 'All', 'book': 'Ebook', 'model': 'Part'}
    if resource_type not in types:
        raise ValueError('resource_type 须为 all、book 或 model')
    url = BASE + '/web/normalRetrieval/' + types[resource_type] + '?' + urlencode({'searchq': keyword, 'currentPage': int(page), 'showCount': 10})
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '25', url], capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError('CIDP 查询失败: ' + p.stderr.strip())
    match = re.search('找到约\\s*(\\d+)\\s*条结果', p.stdout)
    if not match:
        raise RuntimeError('未识别 CIDP 检索结果；网站可能要求登录或页面结构变化')
    total = int(match.group(1))
    parser = Parser()
    parser.feed(p.stdout)
    if not parser.table_seen or parser.bad_rows:
        raise RuntimeError('CIDP 结果表缺失或存在无法识别的题录，网站结构可能已变化')
    if total > 0 and (not parser.items) and ((int(page) - 1) * 10 < total):
        raise RuntimeError('网站显示有结果但没有识别题录')
    if resource_type != 'all' and any((not x['url'].startswith(BASE + '/web/' + types[resource_type] + '/') for x in parser.items)):
        raise RuntimeError('题录类型与请求不一致')
    result = {'source': 'CIDP制造业数字资源平台', 'keyword': keyword, 'page': int(page), 'approximate_total': total, 'items': parser.items, 'scope': '全部资源公开检索页，混合模型、图书等题录；无机构身份或资源全文权限的证明'}
    if resource_type != 'all':
        result['resource_type_requested'] = resource_type
        result['scope'] = '站方类型检索的公开题录；总数为近似值，站方未回显页码；不证明学校机构身份、全文或模型下载权限。'
    return result
if __name__ == '__main__':
    import argparse, json
    p = argparse.ArgumentParser()
    p.add_argument('keyword')
    p.add_argument('--page', type=int, default=1)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.page), ensure_ascii=False, indent=2))
