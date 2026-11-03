"""国家统计局房地产开发和销售的累计报告及原表。"""
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
        if '全国房地产市场基本情况' in title and u.scheme == 'https' and (u.netloc == 'www.stats.gov.cn') and PATH.fullmatch(u.path):
            self.items[url] = {'title': title, 'url': url}

def realestate_list(page=1):
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

def realestate_detail(url, keyword=''):
    u = urlsplit(url)
    if u.scheme != 'https' or u.netloc != 'www.stats.gov.cn' or u.query or u.fragment or (not PATH.fullmatch(u.path)):
        raise ValueError('仅支持国家统计局最新发布栏目的官方详情 URL')
    if not isinstance(keyword, str) or len(keyword) > 60:
        raise ValueError('关键词须不超过 60 字符')
    html = _get(url)
    if '全国房地产市场基本情况' not in html:
        raise ValueError('不是可识别的房地产市场报告')
    p = _LeafTables()
    p.feed(html)
    tables = p.tables
    if len(tables) == 6 and all((tables[i] == tables[i + 3] for i in range(3))):
        tables = tables[:3]
    if len(tables) != 3:
        raise ValueError('上游表格数量或移动版重复结构变化')
    sections = ['全国开发和销售情况', '分地区开发投资', '分地区商品房销售']
    headers = [1, 2, 3]
    out = []
    for name, table, header_n in zip(sections, tables, headers):
        if len(table) <= header_n:
            raise ValueError('未识别官方表头')
        rows = [r for r in table[header_n:] if len(r) > 1]
        notes = [r for r in table[header_n:] if len(r) == 1]
        if keyword:
            rows = [r for r in rows if r and keyword.replace(' ', '') in r[0]['text'].replace(' ', '')]
        out.append({'section': name, 'header_rows': table[:header_n], 'rows': rows, 'note_rows': notes})
    return {'source_url': url, 'keyword': keyword, 'tables': out, 'note': '保留表头和合并属性，指标单位可能为亿元、万平方米或百分比；本地筛选行，具体累计期间、统计范围、可比口径及修订以原报告正文为准。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='command', required=True)
    q = s.add_parser('list')
    q.add_argument('--page', type=int, default=1)
    q = s.add_parser('detail')
    q.add_argument('url')
    q.add_argument('--keyword', default='')
    a = p.parse_args()
    print(json.dumps(realestate_list(a.page) if a.command == 'list' else realestate_detail(a.url, a.keyword), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
