"""中国地质调查局单位动态公开栏目。"""
import release_runtime
import argparse, json, sys, re
from farm_reclamation_adapters import Body, fetch
from html.parser import HTMLParser

class Catalog(HTMLParser):

    def __init__(self):
        super().__init__()
        self.items = {}

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        h = a.get('href', '')
        title = a.get('title', '').strip()
        if t == 'a' and title and re.fullmatch('\\./\\d{6}/t\\d{8}_\\d+\\.html', h):
            self.items[h[2:]] = {'path': h[2:], 'title': title}
BASE = 'https://www.cgs.gov.cn/ywdt/dwdt/'

def geological_updates(keyword=''):
    p = Catalog()
    p.feed(fetch(BASE))
    if not p.items:
        raise ValueError('未识别目录')
    items = [dict(i, url=BASE + i['path']) for i in p.items.values() if keyword in i['title']]
    return {'source': '中国地质调查局单位动态', 'source_url': BASE, 'items': items, 'note': '仅当前首页标题筛选，非地质调查成果数据库或全站搜索。'}

def geological_update_detail(path):
    matches = [i for i in geological_updates()['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在当前首页')
    p = Body()
    p.feed(fetch(matches[0]['url']))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if not text:
        raise ValueError('未识别正文')
    return {'source': '中国地质调查局单位动态', **matches[0], 'text': text, 'note': '公开新闻正文，图表、附件与事实细节以原文为准。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(geological_updates(a.keyword) if a.cmd == 'list' else geological_update_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
