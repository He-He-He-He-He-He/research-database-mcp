"""国家新闻出版署游戏审批信息公开搜索及详情。"""
import release_runtime
import json, re, subprocess
from html.parser import HTMLParser
from urllib.parse import urlparse
BASE = 'https://www.nppa.gov.cn'

def nppa_game_search(title='', publisher='', operator='', description='', page=1):
    page = int(page)
    if page < 1 or page > 10000:
        raise ValueError('页码必须在 1—10000')
    if not any((str(x).strip() for x in (title, publisher, operator, description))):
        raise ValueError('至少输入一个搜索条件')
    args = ['curl', '--fail', '--silent', '--show-error', '--max-time', '25', '--max-redirs', '0', '--request', 'POST', BASE + '/was5/web/search?channelid=288556']
    for k, v in {'page': page, 'size': 20, 'mc': title, 'cbdw': publisher, 'yydw': operator, 'description': description}.items():
        args += ['--data-urlencode', f'{k}={v}']
    obj = json.loads(release_runtime.run(args, check=True, capture_output=True).stdout.decode('utf-8-sig').strip())
    if not isinstance(obj.get('data'), list) or not isinstance(obj.get('total'), int):
        raise ValueError('上游查询格式异常')
    return {'page': page, 'page_size': 20, 'total': obj['total'], 'results': obj['data']}

class _Table(HTMLParser):

    def __init__(self):
        super().__init__()
        self.table = False
        self.row = None
        self.cell = None
        self.rows = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'table' and 'trStyle' in a.get('class', '').split():
            self.table = True
        elif self.table and tag == 'tr':
            self.row = []
        elif self.table and self.row is not None and (tag == 'td'):
            self.cell = []

    def handle_data(self, text):
        if self.cell is not None:
            self.cell.append(text)

    def handle_endtag(self, tag):
        if tag == 'td' and self.cell is not None:
            self.row.append(' '.join(''.join(self.cell).split()))
            self.cell = None
        elif tag == 'tr' and self.row is not None:
            if len(self.row) == 2:
                self.rows.append(self.row)
            self.row = None
        elif tag == 'table' and self.table:
            self.table = False

def nppa_game_detail(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.nppa.gov.cn' or (not re.fullmatch('/bsfw/jggs/cxjg/\\d{6}/t\\d{8}_\\d+\\.html', p.path)) or p.query or p.fragment:
        raise ValueError('仅支持新闻出版署游戏审批查询结果详情')
    raw = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '25', '--max-redirs', '0', url], check=True, capture_output=True).stdout.decode('utf-8-sig')
    p = _Table()
    p.feed(raw)
    if not p.rows:
        raise ValueError('未找到审批详情表')
    return {'url': url, 'fields': p.rows}
