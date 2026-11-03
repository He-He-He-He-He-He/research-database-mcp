"""国家电影局电影备案立项及公映许可查询。"""
import release_runtime
import json, re, subprocess
from html.parser import HTMLParser
from urllib.parse import urlparse
BASE = 'https://www.chinafilm.gov.cn'

def _query(channel, fields, page):
    if isinstance(page, bool) or not (isinstance(page, int) or (isinstance(page, str) and page.isascii() and page.isdigit())):
        raise ValueError('页码须为整数')
    page = int(page)
    if page < 1 or page > 10000:
        raise ValueError('页码需在 1—10000')
    args = ['curl', '--fail', '--silent', '--show-error', '--max-time', '25', '--max-redirs', '0', '--request', 'POST', f'{BASE}/was5/web/search?channelid={channel}']
    for k, v in {'page': page, 'size': 20, **fields}.items():
        args += ['--data-urlencode', f'{k}={v}']
    raw = release_runtime.run(args, check=True, capture_output=True).stdout.decode('utf-8-sig').strip()
    data = json.loads(raw)
    if not isinstance(data, dict) or not isinstance(data.get('data'), list) or type(data.get('total')) is not int or (data['total'] < 0):
        raise ValueError('查询结果格式异常')
    if len(data['data']) > min(20, max(0, data['total'] - (page - 1) * 20)):
        raise ValueError('查询结果数量与总数或页码矛盾')
    return {'page': page, 'page_size': 20, 'total': data['total'], 'results': data['data']}

def film_filing_search(title='', filing_number='', company='', writer='', page=1):
    return _query('256296', {'pmin': title, 'balx': filing_number, 'badw': company, 'biju': writer}, page)

def film_screening_search(title='', code='', permit_number='', company='', page=1):
    return _query('237314', {'pmin': title, 'bima': code, 'gyzh': permit_number, 'cpdw': company}, page)

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

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

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

def film_filing_detail(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.chinafilm.gov.cn' or (not re.fullmatch('/dybalxgs/\\d{6}/t\\d{8}_\\d+\\.html', p.path)) or p.query or p.fragment:
        raise ValueError('仅支持国家电影局备案立项详情地址')
    raw = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '25', '--max-redirs', '0', url], check=True, capture_output=True).stdout.decode('utf-8-sig')
    parser = _Table()
    parser.feed(raw)
    if not parser.rows:
        raise ValueError('未找到备案详情表')
    return {'url': url, 'fields': parser.rows}

def film_distributor_registry(company='', permit_number='', page=1):
    """电影发行经营许可证登记公示的服务端分页查询。"""
    if not company.strip() and (not permit_number.strip()):
        raise ValueError('请至少提供公司名称或发行证号；上游空查询不返回全量')
    return _query('240921', {'gsmc': company, 'zhao': permit_number}, page)
