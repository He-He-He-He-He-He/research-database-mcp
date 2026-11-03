"""农业农村部监测预警日报：查询公开的批发均价。"""
import release_runtime
import argparse, html.parser, json, re, subprocess, sys
from urllib.parse import urljoin, urlparse
BASE = 'https://scs.moa.gov.cn/jcyj/'

class LinkParser(html.parser.HTMLParser):

    def __init__(self):
        super().__init__()
        self.active = False
        self.href = ''
        self.title = ''
        self.date = ''
        self.in_date = False
        self.out = []

    def handle_starttag(self, t, attrs):
        d = dict(attrs)
        if t == 'a' and '农产品批发价格200指数' in d.get('title', ''):
            self.active = True
            self.href = d.get('href', '')
            self.title = d['title']
            self.date = ''
        elif self.active and t == 'span' and (d.get('class') == 'sj_gztzri'):
            self.in_date = True

    def handle_data(self, d):
        if self.active and self.in_date:
            self.date += d.strip()

    def handle_endtag(self, t):
        if t == 'span':
            self.in_date = False
        if t == 'a' and self.active:
            self.active = False
            url = urljoin(BASE, self.href)
            if re.fullmatch('\\d{4}-\\d\\d-\\d\\d', self.date) and urlparse(url).hostname == 'scs.moa.gov.cn':
                self.out.append({'date': self.date, 'title': self.title, 'url': url})

class TextParser(html.parser.HTMLParser):

    def __init__(self):
        super().__init__()
        self.skip = 0
        self.parts = []

    def handle_starttag(self, t, a):
        if t in ('script', 'style'):
            self.skip += 1

    def handle_endtag(self, t):
        if t in ('script', 'style') and self.skip:
            self.skip -= 1

    def handle_data(self, d):
        if not self.skip:
            self.parts.append(d)

def fetch(url):
    r = release_runtime.run(['/usr/bin/curl', '-fsSL', '--max-time', '20', '--user-agent', 'ResearchCatalog/0.1 personal research', url], capture_output=True, check=True)
    return r.stdout.decode('utf-8')

def listing(page=1):
    if not 1 <= page <= 10:
        raise ValueError('页码应在 1 至 10 之间')
    url = BASE if page == 1 else BASE + f'index_{page - 1}.htm'
    p = LinkParser()
    p.feed(fetch(url))
    if not p.out:
        raise ValueError('未获取到日报，目录结构可能改变')
    return p.out

def detail(day=None, page=1):
    items = listing(page)
    rows = [x for x in items if day is None or x['date'] == day]
    if not rows:
        raise ValueError('所选目录页没有该日期；可先 list 查看')
    row = rows[0]
    p = TextParser()
    p.feed(fetch(row['url']))
    text = re.sub('\\s+', '', ''.join(p.parts))

    def capture(pattern):
        m = re.search(pattern, text)
        return m.group(1) if m else None
    price = {}
    raw_price = {}
    for name, pat in [('猪肉', '猪肉平均价格为([\\d.]+)元/公斤'), ('牛肉', '牛肉([\\d.]+)元/公斤'), ('羊肉', '羊肉([\\d.]+)元/公斤'), ('鸡蛋', '鸡蛋([\\d.]+)元/公斤'), ('白条鸡', '白条鸡([\\d.]+)元/公斤'), ('28种蔬菜平均', '28种蔬菜平均价格为([\\d.]+)元/公斤'), ('6种水果平均', '6种水果平均价格为([\\d.]+)元/公斤')]:
        raw_price[name] = capture(pat)
        price[name] = float(raw_price[name]) if raw_price[name] is not None else None
    raw_index = capture('农产品批发价格200指数[”\\"]?为([\\d.]+)')
    index = float(raw_index) if raw_index is not None else None
    if index is None and all((v is None for v in price.values())):
        raise ValueError('日报内容未能解析，页面可能改版')
    return {**row, 'wholesale_index_200': index, 'wholesale_index_200_raw': raw_index, 'prices_yuan_per_kg': price, 'prices_yuan_per_kg_raw': raw_price, 'source': '农业农村部市场与信息化司', 'note': '官方日报公布的全国农产品批发市场均价，通常为当日14时监测；空值表示未能解析，不代表零。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sp = p.add_subparsers(dest='command', required=True)
    q = sp.add_parser('list')
    q.add_argument('--page', type=int, default=1)
    q = sp.add_parser('detail')
    q.add_argument('--date')
    q.add_argument('--page', type=int, default=1)
    a = p.parse_args()
    o = {'items': listing(a.page), 'scope': '所选目录页'} if a.command == 'list' else detail(a.date, a.page)
    print(json.dumps(o, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
