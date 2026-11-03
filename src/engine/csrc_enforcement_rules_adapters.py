"""中国证监会行政执法相关规定公开目录。"""
import release_runtime
import argparse, html, json, re, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from research import get, fetch
BASE = 'https://www.csrc.gov.cn'
CHANNEL = 'cbeeeb265b49417db962bc753c6c8560'

class Article(HTMLParser):

    def __init__(self, base):
        super().__init__()
        self.base = base
        self.depth = 0
        self.seen = False
        self.parts = []
        self.attachments = []
        self.title = ''

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'meta' and a.get('name') == 'ArticleTitle':
            self.title = a.get('content', '')
        if t == 'div' and (not self.depth) and ('detail-news' in a.get('class', '').split()):
            self.depth = 1
            self.seen = True
            return
        if self.depth:
            if t == 'div':
                self.depth += 1
            if t in ('p', 'br'):
                self.parts.append('\n')
            if t == 'a':
                u = urljoin(self.base, a.get('href', ''))
                p = urlparse(u)
                if p.scheme == 'https' and p.netloc == 'www.csrc.gov.cn' and p.path.lower().endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx')):
                    self.attachments.append(u)

    def handle_data(self, d):
        if self.depth:
            self.parts.append(d)

    def handle_endtag(self, t):
        if self.depth and t == 'div':
            self.depth -= 1
        elif self.depth and t == 'p':
            self.parts.append('\n')

def list_rules(page=1, size=5, keyword=''):
    if not 1 <= page <= 10000 or not 1 <= size <= 20:
        raise ValueError('页码须大于零，每页为1至20条')
    data = get(BASE + '/searchList/' + CHANNEL, {'_isAgg': 'true', '_isJson': 'true', '_pageSize': size, '_template': 'index', '_rangeTimeGte': '', '_channelName': '', 'page': page})
    d = data.get('data') if isinstance(data, dict) else None
    if not isinstance(d, dict) or not isinstance(d.get('results'), list):
        raise ValueError('上游 JSON 结构异常')
    items = []
    for x in d['results']:
        title = x.get('title') or ''
        content = html.unescape(x.get('content') or '')
        if keyword.casefold() not in (title + ' ' + content).casefold():
            continue
        url = x.get('url') or ''
        url = 'https:' + url if url.startswith('//') else url
        items.append({'title': title, 'published': x.get('publishedTimeStr'), 'url': url, 'id': str(x.get('manuscriptId', ''))})
    return {'source': BASE + '/csrc/c101926/common_list.shtml?channelid=' + CHANNEL, 'total': d.get('total'), 'page': page, 'items': items, 'scope': '栏目总数；关键词仅匹配本页，包含正式规则和征求意见稿'}

def list_rules_all(keyword='', limit=100, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 100 or type(limit) is not int or (not 1 <= limit <= 200) or (type(offset) is not int) or (not 0 <= offset <= 100000):
        raise ValueError('关键词、limit或offset无效')
    rows = []
    seen = set()
    total = None
    pages = 0
    for page in range(1, 21):
        response = get(BASE + '/searchList/' + CHANNEL, {'_isAgg': 'true', '_isJson': 'true', '_pageSize': 20, '_template': 'index', '_rangeTimeGte': '', '_channelName': '', 'page': page})
        d = response.get('data') if isinstance(response, dict) else None
        if not isinstance(d, dict) or d.get('page') != page or d.get('rows') != 20 or (d.get('channelId') != CHANNEL) or (type(d.get('total')) is not int) or (d['total'] < 0) or (not isinstance(d.get('results'), list)) or (len(d['results']) > 20):
            raise ValueError('上游栏目页响应异常')
        if total is None:
            total = d['total']
        if total != d['total']:
            raise ValueError('读取期间栏目总数变化，请重试')
        for x in d['results']:
            if not isinstance(x, dict):
                raise ValueError('栏目条目异常')
            ident = str(x.get('manuscriptId', ''))
            if not re.fullmatch('[A-Za-z0-9]{1,64}', ident) or ident in seen:
                raise ValueError('栏目条目标识缺失或重复')
            seen.add(ident)
            rows.append(x)
        pages = page
        if len(rows) >= total:
            break
        if not d['results']:
            raise ValueError('栏目数据提前结束')
    else:
        raise ValueError('栏目超过20页上限')
    if len(rows) != total:
        raise ValueError('栏目总数不一致')
    q = keyword.casefold()
    matched = []
    for x in rows:
        title = x.get('title') or ''
        content = html.unescape(x.get('content') or '')
        if q not in (title + ' ' + content).casefold():
            continue
        url = x.get('url') or ''
        url = 'https:' + url if url.startswith('//') else url
        matched.append({'title': title, 'published': x.get('publishedTimeStr'), 'url': url, 'id': str(x['manuscriptId'])})
    return {'source': BASE + '/csrc/c101926/common_list.shtml?channelid=' + CHANNEL, 'total': total, 'source_pages_fetched': pages, 'keyword': keyword, 'matched_total': len(matched), 'limit': limit, 'offset': offset, 'next_offset': offset + limit if offset + limit < len(matched) else None, 'items': matched[offset:offset + limit], 'scope': '逐页读取后本地匹配标题和摘要，最多20源页并检查总数和ID；源站不保证原子快照。包含正式规则和征求意见稿，效力须逐项核实。'}

def detail(url):
    u = urlparse(url)
    if u.scheme != 'https' or u.netloc != 'www.csrc.gov.cn' or (not re.fullmatch('/csrc/c\\d+/c\\d+/content\\.shtml', u.path)) or u.query or u.fragment:
        raise ValueError('只允许证监会同站文章链接')
    p = Article(url)
    p.feed(fetch(url))
    if not p.seen:
        raise ValueError('正文未找到，页面可能改版')
    return {'source': url, 'title': p.title, 'text': ''.join(p.parts).strip(), 'attachments': p.attachments}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('--page', type=int, default=1)
    q.add_argument('--size', type=int, default=5)
    q.add_argument('--keyword', default='')
    q = s.add_parser('detail')
    q.add_argument('url')
    a = p.parse_args()
    print(json.dumps(list_rules(a.page, a.size, a.keyword) if a.cmd == 'list' else detail(a.url), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
