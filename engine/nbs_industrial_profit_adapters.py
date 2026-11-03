"""国家统计局规模以上工业企业财务指标发布表。"""
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
        if '全国规模以上工业企业利润' in title and u.scheme == 'https' and (u.netloc == 'www.stats.gov.cn') and PATH.fullmatch(u.path):
            self.items[url] = {'title': title, 'url': url}

def industrial_profit_list(page=1):
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
    return {'source_url': url, 'items': list(p.items.values()), 'note': '只筛选最新发布栏目指定页，空列表不代表全部历史没有报告。'}

def industrial_profit_detail(url, keyword=''):
    u = urlsplit(url)
    if u.scheme != 'https' or u.netloc != 'www.stats.gov.cn' or u.query or u.fragment or (not PATH.fullmatch(u.path)):
        raise ValueError('仅支持国家统计局最新发布栏目官方详情 URL')
    if not isinstance(keyword, str) or len(keyword) > 60:
        raise ValueError('关键词须不超过 60 字符')
    html = _get(url)
    if '规模以上工业企业利润' not in html:
        raise ValueError('不是可识别的工业企业利润报告')
    p = _LeafTables()
    p.feed(html)
    tables = p.tables
    if len(tables) == 6 and all((tables[i] == tables[i + 3] for i in range(3))):
        tables = tables[:3]
    if len(tables) != 3:
        raise ValueError('上游表格数量或移动版重复结构变化')
    sections = ['主要财务指标', '主要财务指标（续表）', '分行业主要财务指标']
    header_counts = [2, 3, 3]
    out = []
    for name, table, header_n in zip(sections, tables, header_counts):
        if len(table) <= header_n or not any(('营业收入' in c['text'].replace(' ', '') for c in table[0])):
            raise ValueError('未识别官方表头')
        rows = [r for r in table[header_n:] if len(r) > 1]
        notes = [r for r in table[header_n:] if len(r) == 1]
        if keyword:
            rows = [r for r in rows if r and keyword.replace(' ', '') in r[0]['text'].replace(' ', '')]
        out.append({'section': name, 'header_rows': table[:header_n], 'rows': rows, 'note_rows': notes})
    return {'source_url': url, 'keyword': keyword, 'tables': out, 'note': '保留原始单元格、分组和合并属性，所有金额、增长率、利润率及效率指标的期间与单位以原表表头为准；本地行筛选，不代表全站搜索。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='command', required=True)
    q = s.add_parser('list')
    q.add_argument('--page', type=int, default=1)
    q = s.add_parser('detail')
    q.add_argument('url')
    q.add_argument('--keyword', default='')
    a = p.parse_args()
    print(json.dumps(industrial_profit_list(a.page) if a.command == 'list' else industrial_profit_detail(a.url, a.keyword), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
