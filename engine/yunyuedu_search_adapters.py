"""浙大芸悦读新书目录查询：仅书目元数据。"""
import release_runtime
import json, re, subprocess
from html.parser import HTMLParser
from urllib.parse import urlencode
BASE = 'http://www.yuntaigo.com/'

def curl(args, cookie=None):
    config = None
    if cookie is not None:
        if '\n' in cookie or '\r' in cookie:
            raise ValueError('网站会话格式不合法')
        config = 'cookie = "' + cookie.replace('\\', '\\\\').replace('"', '\\"') + '"\n'
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '25', *(['--config', '-'] if cookie is not None else []), *args], input=config, capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError('芸悦读站点请求失败: ' + p.stderr.strip())
    return p.stdout

def session_cookie():
    jar = curl(['--cookie-jar', '-', '--output', '/dev/null', BASE + 'zju.html'])
    parts = []
    for line in jar.splitlines():
        if line.startswith('#HttpOnly_'):
            line = line[len('#HttpOnly_'):]
        if not line or line.startswith('#'):
            continue
        cols = line.split('\t')
        if len(cols) == 7:
            parts.append(cols[5] + '=' + cols[6])
    if not parts:
        raise RuntimeError('网站没有创建查询会话')
    return '; '.join(parts)

class Results(HTMLParser):

    def __init__(self):
        super().__init__()
        self.items = []
        self.ids = set()
        self.count = None
        self.page_size = None
        self.bad = 0

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'input' and a.get('id') == 'pagecount':
            self.count = a.get('value')
        if t == 'input' and a.get('id') == 'pagesize':
            self.page_size = a.get('value')
        if t == 'a' and 'xinbook' in a.get('class', '').split():
            href = a.get('href', '')
            m = re.fullmatch('book\\.action\\?recordid=([A-Za-z0-9+/=_-]+)', href)
            title = (a.get('title') or '').strip()
            if not m or not title:
                self.bad += 1
                return
            id = m.group(1)
            if id not in self.ids:
                self.ids.add(id)
                self.items.append({'id': id, 'title': title, 'url': BASE + 'client/book.action?' + urlencode({'recordid': id})})

class BookDetail(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.seen = False
        self.title = ''
        self.info = []
        self.current = None

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'input' and a.get('id') == 'booktitle':
            self.title = (a.get('value') or '').strip()
        if self.depth:
            if t == 'div':
                self.depth += 1
            if t == 'p':
                self.current = []
            if t == 'br' and self.current is not None:
                self.current.append('\n')
        elif t == 'div' and 'bookinfoList' in a.get('class', '').split():
            self.seen = True
            self.depth = 1

    def handle_data(self, s):
        if self.current is not None:
            self.current.append(s)

    def handle_endtag(self, t):
        if self.depth and t == 'p' and (self.current is not None):
            self.info.extend((x.strip() for x in ''.join(self.current).splitlines() if x.strip()))
            self.current = None
        if self.depth and t == 'div':
            self.depth -= 1

def detail(record_id):
    if not isinstance(record_id, str) or not re.fullmatch('[A-Za-z0-9+/=_-]{1,200}', record_id):
        raise ValueError('请提供书目查询返回的资源编号')
    cookie = session_cookie()
    url = BASE + 'client/book.action?' + urlencode({'recordid': record_id})
    body = curl([url], cookie)
    p = BookDetail()
    p.feed(body)
    if not p.seen or not p.title or (not p.info):
        raise RuntimeError('书目详情不完整或网站结构变化')
    return {'source': '浙大芸悦读', 'id': record_id, 'title': p.title, 'bibliographic_details': p.info, 'url': url, 'scope': '官网显示的书目信息；未验证购买、借阅、全文或馆藏状态', 'note': '网站使用明文 HTTP；勿提交敏感信息。该工具不提交选书或购买请求。'}

def search(keyword, page=1):
    if not isinstance(keyword, str) or not keyword.strip() or (not 1 <= int(page) <= 1000):
        raise ValueError('请输入关键词，页码须为正整数')
    cookie = session_cookie()
    q = {'sfield': 'ALL', 'keyword': keyword, 'framflag': '1'}
    first = curl(['--get', *sum((['--data-urlencode', k + '=' + v] for k, v in q.items()), []), BASE + 'client/yunreadsearch.action'], cookie)
    p = Results()
    p.feed(first)
    if p.count is None or not str(p.count).isdigit() or p.page_size != '15' or p.bad:
        raise RuntimeError('检索结果页不完整或格式变化')
    pages = int(p.count)
    if int(page) > 1:
        if int(page) > pages:
            return {'source': '浙大芸悦读', 'keyword': keyword, 'page': int(page), 'page_count': pages, 'items': [], 'scope': '当前书目查询页，页码超出当前页数；不代表平台无其他数据', 'note': '网站使用明文 HTTP；勿提交敏感信息。未验证阅读、借阅、订购或全文权限。'}
        url = BASE + 'client/yunreadsearch_page.action?' + urlencode({'pagenum': 10, 'pager.offset': (int(page) - 1) * 15, 'sign': 'zhongtu'})
        body = curl([url], cookie)
        p = Results()
        p.feed(body)
        current = re.search('当前第\\s*<span>\\s*(\\d+)\\s*</span>', body)
        if p.bad or p.count is None or int(p.count) != pages or (not current) or (int(current.group(1)) != int(page)):
            raise RuntimeError('实际页码或结果结构不匹配')
    if pages > 0 and (not p.items):
        raise RuntimeError('网站显示有结果但未识别书目')
    return {'source': '浙大芸悦读', 'keyword': keyword, 'page': int(page), 'page_count': pages, 'items': p.items, 'scope': '网站全部字段书目搜索，页数为网站返回，不提供总条数；未验证阅读、借阅、订购或全文权限', 'note': '网站使用明文 HTTP；勿提交敏感信息。该工具不提交选书或购买请求。'}
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('keyword', nargs='?', default='')
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--detail')
    a = p.parse_args()
    print(json.dumps(detail(a.detail) if a.detail else search(a.keyword, a.page), ensure_ascii=False, indent=2))
