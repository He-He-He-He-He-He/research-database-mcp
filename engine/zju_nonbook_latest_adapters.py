"""浙大非书资料系统首页“最新收录”仅五条公开题目。"""
import release_runtime
import http.cookiejar, json, re, urllib.request
from html.parser import HTMLParser
from urllib.parse import urlencode
BASE = 'http://210.32.137.198/'

class Parser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.box = 0
        self.active = False
        self.items = []
        self.seen = False
        self.bad = 0

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        classes = a.get('class', '').split()
        if t == 'div' and 'shoulu' in classes:
            self.box = 1
            self.seen = True
        elif self.box and t == 'div':
            self.box += 1
        if self.box and t == 'li' and ('shoul' in classes):
            self.active = True
        if self.active and t == 'a':
            m = re.fullmatch('showpage\\.do\\?status=show&METAID=(\\d+)', a.get('href', ''))
            if not m or not (a.get('title') or '').strip():
                self.bad += 1
            else:
                self.items.append({'title': a['title'].strip(), 'id': m.group(1), 'url': BASE + 'showpage.do?' + urlencode({'status': 'show', 'METAID': m.group(1)})})

    def handle_endtag(self, t):
        if t == 'li' and self.active:
            self.active = False
        if t == 'div' and self.box:
            self.box -= 1

def latest(keyword=''):
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    try:
        with opener.open(BASE, timeout=20) as r:
            body = r.read().decode('utf8', 'replace')
    except Exception as e:
        raise RuntimeError('浙大非书资料系统首页请求失败') from e
    p = Parser()
    p.feed(body)
    if not p.seen or p.bad or (not p.items):
        raise RuntimeError('首页最新收录结构异常，未返回不完整目录')
    return {'source': '浙大图书馆非书资料系统首页', 'keyword': keyword, 'page_items': len(p.items), 'items': [x for x in p.items if keyword in x['title']], 'scope': '仅首页最新收录展示，关键词只筛这几条；完整检索、详情、随书光盘和下载权限未验证', 'note': '站点使用明文 HTTP；勿提交敏感信息。站点详情和检索本次返回“系统忙”，链接可能不可用。'}
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('keyword', nargs='?', default='')
    a = p.parse_args()
    print(json.dumps(latest(a.keyword), ensure_ascii=False, indent=2))
