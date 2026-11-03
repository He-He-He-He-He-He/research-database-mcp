"""司法部“复议工作”公开栏目单页目录。"""
import release_runtime
import json, re, ssl, http.cookiejar, urllib.request
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, urlunparse
BASE = 'https://www.moj.gov.cn/pub/sfbgw/fzgz/fzgzxzzf/fzgzfygz/'

class ListParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.in_list = False
        self.seen = False
        self.item = None
        self.in_date = False
        self.in_anchor = False
        self.bad = 0
        self.items = []

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'ul' and 'newsMsgList_zzy' in a.get('class', '').split():
            self.in_list = True
            self.seen = True
        elif self.in_list and t == 'li':
            self.item = {'title': '', 'date': '', 'url': ''}
        elif self.item is not None and t == 'div' and ('rightData' in a.get('class', '').split()):
            self.in_date = True
        elif self.item is not None and t == 'a' and ('leftA' in a.get('class', '').split()):
            p = urlparse(urljoin(BASE, a.get('href', '')))
            if p.hostname == 'www.moj.gov.cn' and p.scheme in ('http', 'https') and p.path.startswith('/pub/sfbgw/fzgz/fzgzxzzf/fzgzfygz/'):
                self.item['url'] = urlunparse(('https', p.netloc, p.path, '', '', ''))
                self.in_anchor = True
            else:
                self.bad += 1

    def handle_data(self, s):
        if self.in_date and self.item is not None:
            self.item['date'] += s.strip()
        if self.in_anchor and self.item is not None:
            self.item['title'] += s

    def handle_endtag(self, t):
        if t == 'div':
            self.in_date = False
        if t == 'a':
            self.in_anchor = False
        if self.in_list and t == 'li' and (self.item is not None):
            self.item['title'] = ' '.join(self.item['title'].split())
            if all(self.item.values()):
                self.items.append(self.item)
            else:
                self.bad += 1
            self.item = None
        if self.in_list and t == 'ul':
            self.in_list = False

def search(keyword='', page=1):
    if not 1 <= int(page) <= 10000:
        raise ValueError('页码须为正整数')
    cafile = '/etc/ssl/cert.pem'
    ctx = ssl.create_default_context(cafile=cafile) if Path(cafile).is_file() else ssl.create_default_context()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()), urllib.request.HTTPSHandler(context=ctx))
    url = BASE + ('index.html' if int(page) == 1 else 'index_' + str(int(page) - 1) + '.html')
    try:
        with opener.open(url, timeout=25) as response:
            body = response.read().decode('utf-8', 'replace')
    except Exception as exc:
        raise RuntimeError('司法部栏目请求失败') from exc
    meta = re.search('createPageHTML\\((\\d+),\\s*(\\d+),\\s*"index",\\s*"html"\\)', body)
    if not meta or int(meta.group(2)) + 1 != int(page):
        raise RuntimeError('司法部栏目页码不匹配或结构已变化')
    p = ListParser()
    p.feed(body)
    if not p.seen or p.bad:
        raise RuntimeError('栏目结果缺失或不完整，网站结构可能变化')
    return {'source': '司法部复议工作栏目', 'page': int(page), 'page_count': int(meta.group(1)), 'keyword': keyword, 'page_items': len(p.items), 'items': [x for x in p.items if keyword in x['title']], 'scope': '只筛选当前页标题；包括工作动态、人物和案例报道，不是全部行政复议案例；以官网原文和现行法律为准'}
if __name__ == '__main__':
    import argparse
    a = argparse.ArgumentParser()
    a.add_argument('keyword', nargs='?', default='')
    a.add_argument('--page', type=int, default=1)
    o = a.parse_args()
    print(json.dumps(search(o.keyword, o.page), ensure_ascii=False, indent=2))
