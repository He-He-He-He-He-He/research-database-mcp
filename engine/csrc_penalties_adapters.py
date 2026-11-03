"""证监会行政处罚公开栏目，结构化列表和正文读取。"""
import release_runtime
import argparse, html, json, re, sys
from html.parser import HTMLParser
from research import fetch, get
BASE = 'https://www.csrc.gov.cn'
CHANNEL = '28de6b87eda140cb93de4dd10d11867d'

class Article(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.seen = False
        self.parts = []
        self.meta = {}

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'meta' and a.get('name') in ('PubDate', 'Description', 'ArticleTitle'):
            self.meta[a['name']] = a.get('content', '')
        if t == 'div' and (not self.depth) and ('detail-news' in a.get('class', '').split()):
            self.depth = 1
            self.seen = True
            return
        if self.depth:
            if t == 'div':
                self.depth += 1
            if t in ('p', 'br'):
                self.parts.append('\n')

    def handle_data(self, d):
        if self.depth:
            self.parts.append(d)

    def handle_endtag(self, t):
        if t == 'div' and self.depth:
            self.depth -= 1
        if t == 'p' and self.depth:
            self.parts.append('\n')

def list_decisions(page=1, size=5, keyword=''):
    if not 1 <= page <= 10000 or not 1 <= size <= 20:
        raise ValueError('页码须大于零，单页数量须为 1 至 20')
    data = get(BASE + '/searchList/' + CHANNEL, {'_isAgg': 'true', '_isJson': 'true', '_pageSize': size, '_template': 'index', '_rangeTimeGte': '', '_channelName': '', 'page': page})
    if not isinstance(data, dict) or not isinstance(data.get('data'), dict) or (not isinstance(data['data'].get('results'), list)):
        raise ValueError('上游返回的栏目数据结构异常')
    d = data['data']
    items = []
    for x in d['results']:
        raw = html.unescape(x.get('content') or '')
        title = x.get('title') or ''
        if keyword.casefold() not in (title + ' ' + raw).casefold():
            continue
        url = x.get('url', '')
        url = 'https:' + url if url.startswith('//') else url
        items.append({'id': str(x.get('manuscriptId', '')), 'title': title, 'published': x.get('publishedTimeStr'), 'url': url})
    return {'source': BASE + '/csrc/c101928/common_list.shtml?channelid=' + CHANNEL, 'page': page, 'size': size, 'total': d.get('total'), 'items': items, 'scope': '关键词只过滤上游返回的当前页标题和摘要，不是全库检索'}

def search_pages(keyword='', start_page=1, end_page=3, size=5):
    if not isinstance(keyword, str):
        raise ValueError('关键词须为字符串')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (start_page, end_page, size))) or not 1 <= start_page <= end_page <= 10000 or end_page - start_page >= 20 or (not 1 <= size <= 20):
        raise ValueError('页码范围不合法，每次最多 20 页，单页 1–20 条')
    items = []
    seen = set()
    total = None
    for page in range(start_page, end_page + 1):
        result = list_decisions(page, size, keyword)
        if not isinstance(result['total'], int) or isinstance(result['total'], bool) or result['total'] < 0:
            raise ValueError('上游总数无效')
        if total is None:
            total = result['total']
        elif total != result['total']:
            raise ValueError('跨页总数变化，请重新查询')
        for item in result['items']:
            if not item['id'] or item['id'] in seen:
                raise ValueError('命中条目的编号缺失或重复，目录可能发生变化')
            seen.add(item['id'])
            items.append(item)
    return {'source': result['source'], 'keyword': keyword, 'start_page': start_page, 'end_page': end_page, 'size': size, 'upstream_total': total, 'matched_count': len(items), 'items': items, 'scope': '仅筛选所选页标题和上游摘要；源总数不是命中总数，也不是全文搜索。目录动态变化，跨页非原子快照，不能认定覆盖全部处罚。'}

def detail(id):
    if not re.fullmatch('\\d{1,12}', str(id)):
        raise ValueError('文书 ID 须为数字')
    url = BASE + '/csrc/c101928/c' + str(id) + '/content.shtml'
    p = Article()
    p.feed(fetch(url))
    if not p.seen:
        raise ValueError('未找到正文，页面可能变更')
    return {'source': url, 'meta': p.meta, 'text': ''.join(p.parts).strip()}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('--page', type=int, default=1)
    q.add_argument('--size', type=int, default=5)
    q.add_argument('--keyword', default='')
    q = s.add_parser('search-pages')
    q.add_argument('--keyword', default='')
    q.add_argument('--start-page', type=int, default=1)
    q.add_argument('--end-page', type=int, default=3)
    q.add_argument('--size', type=int, default=5)
    q = s.add_parser('detail')
    q.add_argument('id')
    a = p.parse_args()
    print(json.dumps(list_decisions(a.page, a.size, a.keyword) if a.cmd == 'list' else search_pages(a.keyword, a.start_page, a.end_page, a.size) if a.cmd == 'search-pages' else detail(a.id), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
