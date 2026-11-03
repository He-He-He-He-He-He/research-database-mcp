"""生态环境部全国空气和地表水质量月报目录，只读。"""
import release_runtime
import argparse, json, re, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from research import fetch
BASE = {'air': 'https://www.mee.gov.cn/hjzl/dqhj/cskqzlzkyb/', 'water': 'https://www.mee.gov.cn/hjzl/shj/dbsszyb/'}

class Listing(HTMLParser):

    def __init__(self, base):
        super().__init__()
        self.base = base
        self.date = ''
        self.dateon = False
        self.url = None
        self.text = []
        self.items = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'span' and 'date' in a.get('class', '').split():
            self.dateon = True
            self.date = ''
        if tag == 'a' and re.fullmatch('\\./\\d{6}/t\\d{8}_\\d+\\.shtml', a.get('href', '')):
            self.url = urljoin(self.base, a['href'])
            self.text = []

    def handle_data(self, s):
        if self.dateon:
            self.date += s
        if self.url:
            self.text.append(s)

    def handle_endtag(self, tag):
        if tag == 'span':
            self.dateon = False
        if tag == 'a' and self.url:
            title = ' '.join(''.join(self.text).split())
            if '月' in title and ('空气质量' in title or '水质' in title):
                self.items.append({'title': title, 'date': self.date.strip(), 'url': self.url})
            self.url = None

class Detail(HTMLParser):

    def __init__(self, base):
        super().__init__()
        self.base = base
        self.title = ''
        self.pdf = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and a.get('name') == 'ArticleTitle':
            self.title = a.get('content', '')
        if tag == 'a' and re.fullmatch('\\./W\\d+\\.pdf', a.get('href', ''), re.I):
            self.pdf.append(urljoin(self.base, a['href']))

def report_list(kind, page=1, keyword=''):
    if kind not in BASE or not 1 <= page <= 100:
        raise ValueError('报告种类或页码无效')
    base = BASE[kind]
    url = base if page == 1 else base + 'index_' + str(page - 1) + '.shtml'
    p = Listing(base)
    p.feed(fetch(url))
    if not p.items:
        raise ValueError('未找到月报，可能超出页数或网页结构变化')
    return {'source': '生态环境部', 'kind': kind, 'page': page, 'source_url': url, 'items': [x for x in p.items if keyword in x['title']], 'note': '仅筛选当前页目录；详情链接提供 PDF 原件地址。'}

def report_search_pages(kind, keyword='', start_page=1, end_page=3):
    if kind not in BASE or not isinstance(keyword, str):
        raise ValueError('报告种类或关键词无效')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (start_page, end_page))) or not 1 <= start_page <= end_page <= 100 or end_page - start_page >= 20:
        raise ValueError('起止页须为 1–100 的整数，最多查询连续 20 页')
    items = []
    sources = []
    seen = set()
    for page in range(start_page, end_page + 1):
        result = report_list(kind, page, keyword)
        sources.append(result['source_url'])
        for item in result['items']:
            if item['url'] in seen:
                raise ValueError('跨页出现重复链接，目录可能已更新；请重新查询')
            seen.add(item['url'])
            items.append(item)
    return {'source': '生态环境部', 'kind': kind, 'keyword': keyword, 'start_page': start_page, 'end_page': end_page, 'source_urls': sources, 'matched_count': len(items), 'items': items, 'note': '仅筛选指定范围标题；目录动态变化，跨页非原子快照，不代表全部历史。详情返回 PDF 原件链接但未读取 PDF，具体数据和统计口径须读原件。'}

def report_detail(url):
    x = urlsplit(url)
    prefixes = ['/hjzl/dqhj/cskqzlzkyb/', '/hjzl/shj/dbsszyb/']
    if x.scheme != 'https' or x.netloc != 'www.mee.gov.cn' or x.query or x.fragment or (not any((re.fullmatch(re.escape(p) + '\\d{6}/t\\d{8}_\\d+\\.shtml', x.path) for p in prefixes))):
        raise ValueError('只接受本模块月报目录的官网详情地址')
    p = Detail(url)
    p.feed(fetch(url))
    if not p.title or not p.pdf:
        raise ValueError('未识别月报 PDF，网页可能改版')
    return {'source_url': url, 'title': p.title, 'pdf_urls': p.pdf, 'note': '链接为官方报告原件；未下载或解析其中具体监测数据。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('kind', choices=list(BASE))
    q.add_argument('--page', type=int, default=1)
    q.add_argument('--keyword', default='')
    q = s.add_parser('search-pages')
    q.add_argument('kind', choices=list(BASE))
    q.add_argument('--keyword', default='')
    q.add_argument('--start-page', type=int, default=1)
    q.add_argument('--end-page', type=int, default=3)
    q = s.add_parser('detail')
    q.add_argument('url')
    a = p.parse_args()
    print(json.dumps(report_list(a.kind, a.page, a.keyword) if a.cmd == 'list' else report_search_pages(a.kind, a.keyword, a.start_page, a.end_page) if a.cmd == 'search-pages' else report_detail(a.url), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
