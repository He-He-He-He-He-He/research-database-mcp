"""国家统计局 CPI / PPI 公开报告及原始主要数据表。"""
import release_runtime
import argparse
from html.parser import HTMLParser
import json
import re
import subprocess
from urllib.parse import urljoin, urlsplit
from moe_education_statistics_adapters import _LeafTables
ROOT = 'https://www.stats.gov.cn'
INDEX = ROOT + '/sj/zxfb/'
PATH = re.compile('/sj/zxfb/\\d{6}/t\\d{8}_\\d+\\.html')

def _get(url):
    return release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], check=True, capture_output=True).stdout.decode('utf-8')

class _Index(HTMLParser):

    def __init__(self):
        super().__init__()
        self.items = {}
        self.release_urls = set()

    def handle_starttag(self, tag, attrs):
        if tag != 'a':
            return
        a = dict(attrs)
        title = a.get('title', '')
        url = urljoin(INDEX, a.get('href', ''))
        u = urlsplit(url)
        if title and u.scheme == 'https' and (u.netloc == 'www.stats.gov.cn') and PATH.fullmatch(u.path):
            self.release_urls.add(url)
        kind = 'CPI' if re.search('居民消费价格同比', title) else 'PPI' if re.search('工业生产者出厂价格同比', title) else ''
        if kind and u.scheme == 'https' and (u.netloc == 'www.stats.gov.cn') and PATH.fullmatch(u.path):
            self.items[url] = {'title': title, 'kind': kind, 'url': url}

def price_release_list(kind='', page=1):
    if kind not in ('', 'CPI', 'PPI'):
        raise ValueError('类别须为 CPI 或 PPI')
    if not isinstance(page, int) or isinstance(page, bool) or (not 1 <= page <= 20):
        raise ValueError('页码须为 1–20')
    index_url = INDEX if page == 1 else INDEX + f'index_{page - 1}.html'
    p = _Index()
    p.feed(_get(index_url))
    items = [x for x in p.items.values() if not kind or x['kind'] == kind]
    if not p.release_urls:
        raise ValueError('未识别官方发布目录，可能是上游格式变化或访问受限')
    return {'source_url': index_url, 'items': items, 'notice': '本页未匹配指定价格报告，可能在其他页；仍需核对网站标题格式。' if not items else None, 'note': '仅国家统计局最新发布目录指定页，不是全部历史月份。'}

def price_release_search_pages(kind='', start_page=1, end_page=5):
    """在指定的连续目录页内查找；这不是完整历史检索。"""
    if kind not in ('', 'CPI', 'PPI'):
        raise ValueError('类别须为 CPI 或 PPI')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (start_page, end_page))) or not 1 <= start_page <= end_page <= 20:
        raise ValueError('起止页须为 1–20 的整数且起页不大于止页')
    items = []
    seen = set()
    sources = []
    for page in range(start_page, end_page + 1):
        result = price_release_list(kind, page)
        sources.append(result['source_url'])
        for item in result['items']:
            if item['url'] in seen:
                raise ValueError('跨页出现重复链接，目录可能已更新；请重新查询')
            seen.add(item['url'])
            items.append(item)
    return {'kind': kind, 'start_page': start_page, 'end_page': end_page, 'source_urls': sources, 'matched_count': len(items), 'items': items, 'note': '仅筛选指定页的标题；目录可能实时更新，跨页并非原子快照，不能证明已覆盖全部历史或最新报告。标题格式变化时可能漏报。'}

def price_release_detail(url, keyword=''):
    u = urlsplit(url)
    if u.scheme != 'https' or u.netloc != 'www.stats.gov.cn' or u.query or u.fragment or (not PATH.fullmatch(u.path)):
        raise ValueError('仅支持国家统计局最新发布栏目的官方详情 URL')
    if not isinstance(keyword, str) or len(keyword) > 60:
        raise ValueError('关键词过长')
    html = _get(url)
    p = _LeafTables()
    p.feed(html)
    all_tables = p.tables
    if len(all_tables) == 2 and all_tables[0] == all_tables[1]:
        all_tables = all_tables[:1]
    if len(all_tables) != 1 or len(all_tables[0]) < 2:
        raise ValueError('页面表格结构变化或不是 CPI/PPI 报告')
    header = all_tables[0][0]
    column = ''.join((x['text'] for x in header))
    first = ''.join((x['text'] for x in all_tables[0][1]))
    if '环比涨跌幅' not in column or '同比涨跌幅' not in column or (not any((x in first for x in ('居民消费价格', '工业生产者出厂价格')))):
        raise ValueError('未识别 CPI/PPI 官方数据表')
    rows = all_tables[0][1:]
    if keyword:
        rows = [r for r in rows if r and keyword in r[0]['text']]
    return {'source_url': url, 'header': header, 'rows': rows, 'keyword': keyword, 'note': '原表数据为百分比涨跌幅而非基期=100的指数；保留原文及单元格属性。关键词仅筛选所选报告中的行，缺失不是零；具体基期与分类以报告说明为准。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='command', required=True)
    q = s.add_parser('list')
    q.add_argument('--kind', choices=['CPI', 'PPI'], default='')
    q.add_argument('--page', type=int, default=1)
    q = s.add_parser('search-pages')
    q.add_argument('--kind', choices=['CPI', 'PPI'], default='')
    q.add_argument('--start-page', type=int, default=1)
    q.add_argument('--end-page', type=int, default=5)
    q = s.add_parser('detail')
    q.add_argument('url')
    q.add_argument('--keyword', default='')
    a = p.parse_args()
    result = price_release_list(a.kind, a.page) if a.command == 'list' else price_release_search_pages(a.kind, a.start_page, a.end_page) if a.command == 'search-pages' else price_release_detail(a.url, a.keyword)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
