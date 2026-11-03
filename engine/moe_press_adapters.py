"""教育部新闻发布会年度目录和图文直播原始 JSON。"""
import release_runtime
import json, re, subprocess
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
BASE = 'http://www.moe.gov.cn'
YEARS = {2022: 'xwfbh_2022n', 2023: 'xwfbh_2023n', 2024: 'xwfbh_2024', 2025: 'xwfbh', 2026: '2026'}

def _get(url):
    p = urlparse(url)
    if p.scheme not in ('http', 'https') or p.hostname != 'www.moe.gov.cn':
        raise ValueError('只读取教育部官网页面')
    return release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '25', '--location', '--max-redirs', '0', url], check=True, capture_output=True).stdout.decode('utf-8-sig')

class _List(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.row = None
        self.capture = None
        self.rows = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'ul' and a.get('id') == 'list':
            self.depth = 1
        elif self.depth and tag == 'ul':
            self.depth += 1
        elif self.depth and tag == 'li':
            self.row = {}
        elif self.row is not None and tag == 'a':
            self.row['url'] = urljoin(BASE, a.get('href', ''))
            self.row['title'] = a.get('title', '')
            self.capture = 'title' if not self.row['title'] else None
        elif self.row is not None and tag == 'span':
            self.capture = 'date'
            self.row['date'] = ''

    def handle_data(self, text):
        if self.row is not None and self.capture:
            self.row[self.capture] += text

    def handle_endtag(self, tag):
        if tag in ('a', 'span'):
            self.capture = None
        elif tag == 'li' and self.row is not None:
            r = self.row
            if r.get('url') and r.get('title'):
                r = {k: v.strip() for k, v in r.items()}
                p = urlparse(r['url'])
                r['图文直播可用路径'] = bool(re.fullmatch('http://www\\.moe\\.gov\\.cn/fbh/live/\\d{4}/\\d+/?', r['url']))
                self.rows.append(r)
            self.row = None
        elif tag == 'ul' and self.depth:
            self.depth -= 1

def moe_press_list(year, keyword='', page=1):
    year = int(year)
    if year not in YEARS:
        raise ValueError('目录仅支持 2022—2026 年')
    page = int(page)
    if page < 1 or page > 100:
        raise ValueError('页码必须在 1—100')
    suffix = '' if page == 1 else f'index_{page - 1}.html'
    p = _List()
    p.feed(_get(f'{BASE}/jyb_xwfb/xw_fbh/moe_2069/{YEARS[year]}/{suffix}'))
    if not p.rows:
        raise ValueError('目录解析为空，页面结构可能变化')
    needle = ''.join(keyword.split()).casefold()
    return [r for r in p.rows if needle in ''.join((''.join(str(v).split()) for v in r.values())).casefold()]

def moe_press_transcript(url):
    p = urlparse(url)
    if p.scheme not in ('http', 'https') or p.hostname != 'www.moe.gov.cn' or (not re.fullmatch('/fbh/live/\\d{4}/\\d+/?', p.path)) or p.query or p.fragment:
        raise ValueError('仅支持教育部官网图文直播详情地址')
    endpoint = f"{BASE}{p.path.rstrip('/')}/tw/data.json"
    rows = json.loads(_get(endpoint))
    if not isinstance(rows, list):
        raise ValueError('直播数据结构发生变化')
    return {'url': url, 'data_url': endpoint, 'entries': rows, 'note': '按网站原顺序保留图文直播各条原始字段，ContentType 区分文字和图片。'}
