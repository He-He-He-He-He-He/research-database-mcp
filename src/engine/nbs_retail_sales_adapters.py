"""国家统计局社会消费品零售总额发布报告及原始表格。"""
import release_runtime
import argparse
from html.parser import HTMLParser
import json
import re
import subprocess
from urllib.parse import urljoin, urlsplit
from moe_education_statistics_adapters import _LeafTables
from nbs_cpi_ppi_release_adapters import _Index as _ReleaseIndex
ROOT = 'https://www.stats.gov.cn'
INDEX = ROOT + '/sj/zxfb/'
PATH = re.compile('/sj/zxfb/\\d{6}/t\\d{8}_\\d+\\.html')

def _get(url):
    return release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], check=True, capture_output=True).stdout.decode('utf-8')

class _Index(HTMLParser):

    def __init__(self):
        super().__init__()
        self.items = {}

    def handle_starttag(self, tag, attrs):
        if tag != 'a':
            return
        a = dict(attrs)
        title = a.get('title', '')
        url = urljoin(INDEX, a.get('href', ''))
        u = urlsplit(url)
        if '社会消费品零售总额' in title and u.scheme == 'https' and (u.netloc == 'www.stats.gov.cn') and PATH.fullmatch(u.path):
            self.items[url] = {'title': title, 'url': url}

def retail_release_list(page=1):
    if not isinstance(page, int) or isinstance(page, bool) or (not 1 <= page <= 20):
        raise ValueError('页码须为 1–20')
    url = INDEX if page == 1 else INDEX + f'index_{page - 1}.html'
    html = _get(url)
    p = _Index()
    p.feed(html)
    guard = _ReleaseIndex()
    guard.feed(html)
    if not guard.release_urls:
        raise ValueError('未识别官方发布目录，可能是页面格式变化或访问受限')
    return {'source_url': url, 'items': list(p.items.values()), 'note': '仅最新发布栏目指定页，空结果不表示历史无报告。'}

def retail_release_search_pages(keyword='', start_page=1, end_page=3):
    if not isinstance(keyword, str):
        raise ValueError('关键词须为字符串')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (start_page, end_page))) or not 1 <= start_page <= end_page <= 20:
        raise ValueError('起止页须为 1–20 的整数')
    items = []
    sources = []
    seen = set()
    for page in range(start_page, end_page + 1):
        result = retail_release_list(page)
        sources.append(result['source_url'])
        for item in result['items']:
            if item['url'] in seen:
                raise ValueError('跨页出现重复链接，目录可能已更新；请重新查询')
            seen.add(item['url'])
            if keyword in item['title']:
                items.append(item)
    return {'source': '国家统计局', 'keyword': keyword, 'start_page': start_page, 'end_page': end_page, 'source_urls': sources, 'matched_count': len(items), 'items': items, 'note': '仅筛选指定页标题；目录动态变化，跨页非原子快照，不代表全部历史。名义增速、报告期和累计时段须核对原表与正文。'}

def retail_release_detail(url, keyword=''):
    u = urlsplit(url)
    if u.scheme != 'https' or u.netloc != 'www.stats.gov.cn' or u.query or u.fragment or (not PATH.fullmatch(u.path)):
        raise ValueError('仅支持国家统计局最新发布栏目官方详情 URL')
    if not isinstance(keyword, str) or len(keyword) > 60:
        raise ValueError('关键词须不超过 60 字符')
    html = _get(url)
    if '社会消费品零售总额' not in html:
        raise ValueError('不是可识别的消费零售报告')
    p = _LeafTables()
    p.feed(html)
    tables = p.tables
    if len(tables) == 4 and tables[0] == tables[2] and (tables[1] == tables[3]):
        tables = tables[:2]
    if len(tables) != 2:
        raise ValueError('表格数量或移动版重复结构变化')
    if len(tables[0]) < 3 or not any(('同比增长' in c['text'] for c in tables[0][1])) or (not any(('环比增速' in c['text'] for c in tables[1][0]))):
        raise ValueError('未识别两表的同比/环比表头')
    sections = ['报告期绝对量及同比', '季节调整月环比']
    header_counts = [2, 1]
    out = []
    for i, (name, table, head) in enumerate(zip(sections, tables, header_counts)):
        rows = [r for r in table[head:] if len(r) > 1]
        notes = [r for r in table[head:] if len(r) == 1]
        if keyword and i == 0:
            rows = [r for r in rows if keyword.replace(' ', '') in r[0]['text'].replace(' ', '')]
        out.append({'section': name, 'header_rows': table[:head], 'rows': rows, 'note_rows': notes})
    return {'source_url': url, 'keyword': keyword, 'tables': out, 'note': '第一表分别保留当月、累计绝对量和同比增速；第二表为季节调整月环比。关键词仅筛第一表，环比表保留合并年份的全部行。各指标单位、时段和名义增速以原表与正文为准。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='command', required=True)
    q = s.add_parser('list')
    q.add_argument('--page', type=int, default=1)
    q = s.add_parser('search-pages')
    q.add_argument('--keyword', default='')
    q.add_argument('--start-page', type=int, default=1)
    q.add_argument('--end-page', type=int, default=3)
    q = s.add_parser('detail')
    q.add_argument('url')
    q.add_argument('--keyword', default='')
    a = p.parse_args()
    print(json.dumps(retail_release_list(a.page) if a.command == 'list' else retail_release_search_pages(a.keyword, a.start_page, a.end_page) if a.command == 'search-pages' else retail_release_detail(a.url, a.keyword), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
