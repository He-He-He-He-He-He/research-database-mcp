"""江苏省水利厅每日水情首页与两个湖泊平均水位。"""
import release_runtime
import argparse, json, re, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from research import fetch
BASE = 'https://jswater.jiangsu.gov.cn'
LIST = BASE + '/col/col55237/index.html'

class Index(HTMLParser):

    def __init__(self):
        super().__init__()
        self.items = []
        self.active = False

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'a' and re.fullmatch('/art/\\d{4}/\\d{1,2}/\\d{1,2}/art_54071_\\d+\\.html', a.get('href', '')):
            self.items.append({'title': '', 'url': urljoin(BASE, a['href'])})
            self.active = True

    def handle_data(self, d):
        if self.active:
            self.items[-1]['title'] += d.strip()

    def handle_endtag(self, t):
        if t == 'a':
            self.active = False

class Body(HTMLParser):

    def __init__(self):
        super().__init__()
        self.active = False
        self.seen = False
        self.parts = []

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'meta' and a.get('name') == 'ContentStart':
            self.active = True
            self.seen = True
        if t == 'meta' and a.get('name') == 'ContentEnd':
            self.active = False
        if self.active and t in ('p', 'br'):
            self.parts.append('\n')

    def handle_data(self, d):
        if self.active:
            self.parts.append(d)

def list_days():
    p = Index()
    p.feed(fetch(LIST))
    p.items = [x for x in p.items if '水情信息' in x['title']]
    if not p.items:
        raise ValueError('未找到水情目录')
    return {'source': LIST, 'scope': '水情目录当前首页', 'items': p.items}

def detail(url):
    u = urlsplit(url)
    if u.scheme != 'https' or u.netloc != 'jswater.jiangsu.gov.cn' or (not re.fullmatch('/art/\\d{4}/\\d{1,2}/\\d{1,2}/art_54071_\\d+\\.html', u.path)) or u.query or u.fragment:
        raise ValueError('仅支持江苏水利厅每日水情文章链接')
    p = Body()
    p.feed(fetch(url))
    if not p.seen:
        raise ValueError('未找到正文')
    text = ''.join(p.parts).strip()
    values = {}
    for name, pattern in [('taihu_average_m', '太湖平均(?:水位)?\\s*(\\d+(?:\\.\\d+)?)米'), ('hongze_average_m', '洪泽湖平均水位\\s*(\\d+(?:\\.\\d+)?)米')]:
        m = re.search(pattern, text)
        values[name] = m.group(1) if m else None
    t = re.search('今日\\s*(\\d{1,2})\\s*时', text)
    return {'source': url, 'article_path_date': '-'.join((str(int(x)) if i else x for i, x in enumerate(u.path.split('/')[2:5]))), 'observation_time': t.group(1) + '时' if t else None, 'values': values, 'raw_text': text, 'note': '仅提取文章中明确标注的湖泊平均水位，缺失为 null；应核对观测时间和原文。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    s.add_parser('list')
    q = s.add_parser('detail')
    q.add_argument('url')
    s.add_parser('latest')
    a = p.parse_args()
    print(json.dumps(list_days() if a.cmd == 'list' else detail(a.url if a.cmd == 'detail' else list_days()['items'][0]['url']), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
