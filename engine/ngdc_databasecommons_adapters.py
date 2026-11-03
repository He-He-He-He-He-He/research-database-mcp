"""国家基因组科学数据中心 Database Commons 生物数据库目录。"""
import release_runtime
import re
import requests
from html.parser import HTMLParser
BASE = 'https://ngdc.cncb.ac.cn/databasecommons/'
SAFE = ('dbId', 'shortName', 'accession', 'fullName', 'description', 'url', 'foundedYear', 'hostInstitution', 'country', 'currentVersion', 'lastUpdate', 'citation')

class _Rows(HTMLParser):

    def __init__(self):
        super().__init__()
        self.in_row = False
        self.in_cell = False
        self.cells = []
        self.parts = []
        self.rows = []

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.in_row = True
            self.cells = []
        elif tag == 'td' and self.in_row:
            self.in_cell = True
            self.parts = []

    def handle_data(self, s):
        if self.in_cell:
            self.parts.append(s)

    def handle_endtag(self, tag):
        if tag == 'td' and self.in_cell:
            self.cells.append(' '.join(''.join(self.parts).split()))
            self.in_cell = False
        elif tag == 'tr' and self.in_row:
            if len(self.cells) == 2:
                self.rows.append(self.cells)
            self.in_row = False

def databasecommons_search(keyword, start=0, length=10):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100 or (not isinstance(start, int)) or (start < 0) or (not isinstance(length, int)) or (not 1 <= length <= 50):
        raise ValueError('请输入关键词及有效分页')
    r = requests.get(BASE + 'database/search', params={'term': keyword, 'draw': 1, 'start': start, 'length': length}, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    x = r.json()
    if not isinstance(x.get('data'), list):
        raise ValueError('未识别数据库检索结果')
    return {'total': x.get('recordsFiltered'), 'items': [{k: v for k, v in a.items() if k in SAFE} for a in x['data']]}

def databasecommons_detail(identifier):
    if not re.fullmatch('\\d{1,12}', str(identifier)):
        raise ValueError('请输入数据库编号')
    u = BASE + 'database/id/' + str(identifier)
    r = requests.get(u, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    p = _Rows()
    p.feed(r.text)
    keys = {'URL', 'Full name', 'Description', 'Year founded', 'Last update', 'Version', 'Accessibility', 'Country/Region', 'University/Institution'}
    data = {a.rstrip(':'): b for a, b in p.rows if a.rstrip(':') in keys}
    if not data.get('Full name') or not data.get('Description'):
        raise ValueError('未识别数据库详情')
    return {'source_url': u, **data}
