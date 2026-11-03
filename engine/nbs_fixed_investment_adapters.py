"""国家统计局固定资产投资公开报告及原始表。"""
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
        if '全国固定资产投资基本情况' in title and u.scheme == 'https' and (u.netloc == 'www.stats.gov.cn') and PATH.fullmatch(u.path):
            self.items[url] = {'title': title, 'url': url}

def investment_list(page=1):
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

def investment_detail(url, keyword=''):
    u = urlsplit(url)
    if u.scheme != 'https' or u.netloc != 'www.stats.gov.cn' or u.query or u.fragment or (not PATH.fullmatch(u.path)):
        raise ValueError('仅支持国家统计局最新发布栏目官方详情 URL')
    if not isinstance(keyword, str) or len(keyword) > 60:
        raise ValueError('关键词须不超过 60 字符')
    html = _get(url)
    if '全国固定资产投资基本情况' not in html:
        raise ValueError('不是可识别的固定资产投资报告')
    p = _LeafTables()
    p.feed(html)
    tables = p.tables
    if len(tables) == 4 and tables[0] == tables[2] and (tables[1] == tables[3]):
        tables = tables[:2]
    if len(tables) != 2:
        raise ValueError('表格数量或移动版重复结构变化')
    if not any(('同比增长' in c['text'] for c in tables[0][0])) or not any(('环比增速' in c['text'] for c in tables[1][0])):
        raise ValueError('未识别两表的同比/环比表头')
    sections = ['报告期累计同比增长', '季节调整环比增速']
    out = []
    for i, (name, table) in enumerate(zip(sections, tables)):
        rows = [r for r in table[1:] if len(r) > 1]
        notes = [r for r in table[1:] if len(r) == 1]
        if keyword:
            if i == 0:
                rows = [r for r in rows if keyword.replace(' ', '') in r[0]['text'].replace(' ', '')]
        out.append({'section': name, 'header_rows': table[:1], 'rows': rows, 'note_rows': notes})
    return {'source_url': url, 'keyword': keyword, 'tables': out, 'note': '首表为累计同比增长率，第二表为季节调整后的月度环比增速；两者均为%，不可互换。关键词仅作用于首表，环比表保持完整，保留合并单元格。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='command', required=True)
    q = s.add_parser('list')
    q.add_argument('--page', type=int, default=1)
    q = s.add_parser('detail')
    q.add_argument('url')
    q.add_argument('--keyword', default='')
    a = p.parse_args()
    print(json.dumps(investment_list(a.page) if a.command == 'list' else investment_detail(a.url, a.keyword), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
