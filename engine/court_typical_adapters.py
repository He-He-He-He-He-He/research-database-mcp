"""最高人民法院官网典型案例发布目录，只读。"""
import release_runtime
import argparse, json, re, sys
from html.parser import HTMLParser
from research import fetch
from legal_adapters import CaseDetail
ROOT = 'https://www.court.gov.cn'

class Listing(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.items = []
        self.date = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if not self.depth and tag == 'div' and ('sec_list' in a.get('class', '').split()):
            self.depth = 1
            return
        if not self.depth:
            return
        if tag == 'div':
            self.depth += 1
        if tag == 'a' and re.fullmatch('/zixun/xiangqing/\\d+\\.html', a.get('href', '')):
            self.items.append({'title': a.get('title', ''), 'url': ROOT + a['href'], 'date': ''})
        if tag == 'i' and 'date' in a.get('class', '').split():
            self.date = True

    def handle_data(self, s):
        if self.date and self.items:
            self.items[-1]['date'] += s.strip()

    def handle_endtag(self, tag):
        if tag == 'i':
            self.date = False
        if self.depth and tag == 'div':
            self.depth -= 1

def typical_list(page=1, keyword=''):
    if not 1 <= page <= 100:
        raise ValueError('页码需在 1–100 之间')
    u = ROOT + '/zixun/gengduo/104' + ('' if page == 1 else '_' + str(page)) + '.html'
    p = Listing()
    p.feed(fetch(u))
    if not p.items:
        raise ValueError('未识别典型案例目录')
    return {'source': '最高人民法院典型案例发布', 'source_url': u, 'page': page, 'items': [x for x in p.items if keyword in x['title']], 'note': '按当前页发布标题筛选；典型案例不等于人民法院案例库全部案例或裁判文书全集。'}

def typical_search_pages(keyword='', start_page=1, end_page=3):
    if not isinstance(keyword, str) or any((type(x) is not int for x in (start_page, end_page))) or (not 1 <= start_page <= end_page <= 100) or (end_page - start_page >= 20):
        raise ValueError('关键词或页码范围无效，每次最多 20 页')
    items = []
    sources = []
    seen = set()
    for page in range(start_page, end_page + 1):
        r = typical_list(page)
        sources.append(r['source_url'])
        for item in r['items']:
            if item['url'] in seen:
                raise ValueError('跨页出现重复链接，目录可能更新；请重新查询')
            seen.add(item['url'])
            if keyword in item['title']:
                items.append(item)
    return {'source': '最高人民法院典型案例发布', 'keyword': keyword, 'start_page': start_page, 'end_page': end_page, 'source_urls': sources, 'matched_count': len(items), 'items': items, 'note': '仅筛选指定页发布标题；目录动态变化，跨页非原子快照，不代表全部历史。条目可能是案例合集，非案例库或裁判文书全集。'}

def typical_detail(id):
    if not re.fullmatch('\\d{1,12}', str(id)):
        raise ValueError('案例发布页面 ID 必须为数字')
    u = ROOT + '/zixun/xiangqing/' + str(id) + '.html'
    p = CaseDetail()
    p.feed(fetch(u))
    if not p.found:
        raise ValueError('未识别典型案例正文')
    return {'source_url': u, 'text': ''.join(p.text).strip(), 'note': '官方案例发布全文；适用性应核对裁判情形及最新法律。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('--page', type=int, default=1)
    q.add_argument('--keyword', default='')
    q = s.add_parser('search-pages')
    q.add_argument('--keyword', default='')
    q.add_argument('--start-page', type=int, default=1)
    q.add_argument('--end-page', type=int, default=3)
    q = s.add_parser('detail')
    q.add_argument('id')
    a = p.parse_args()
    print(json.dumps(typical_list(a.page, a.keyword) if a.cmd == 'list' else typical_search_pages(a.keyword, a.start_page, a.end_page) if a.cmd == 'search-pages' else typical_detail(a.id), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
