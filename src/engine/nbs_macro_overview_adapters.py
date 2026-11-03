"""国家统计局国民经济运行报告及主要指标原表。"""
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

    def handle_starttag(self, tag, attrs):
        if tag != 'a':
            return
        a = dict(attrs)
        title = a.get('title', '')
        url = urljoin(INDEX, a.get('href', ''))
        u = urlsplit(url)
        matched = ('国民经济' in title or '经济运行' in title) and (not any((t in title for t in ('答记者问', '解读', '快报'))))
        if matched and u.scheme == 'https' and (u.netloc == 'www.stats.gov.cn') and PATH.fullmatch(u.path):
            self.items[url] = {'title': title, 'url': url}

def macro_report_list(page=1):
    if not isinstance(page, int) or isinstance(page, bool) or (not 1 <= page <= 20):
        raise ValueError('页码须为 1–20')
    url = INDEX if page == 1 else INDEX + f'index_{page - 1}.html'
    p = _Index()
    p.feed(_get(url))
    return {'source_url': url, 'items': list(p.items.values()), 'note': '仅最新发布栏目指定页，标题候选在详情中再次校验；空列表不代表历史无报告。'}

def macro_report_detail(url, keyword=''):
    u = urlsplit(url)
    if u.scheme != 'https' or u.netloc != 'www.stats.gov.cn' or u.query or u.fragment or (not PATH.fullmatch(u.path)):
        raise ValueError('仅支持国家统计局最新发布栏目的官方详情 URL')
    if not isinstance(keyword, str) or len(keyword) > 60:
        raise ValueError('关键词须不超过 60 字符')
    html = _get(url)
    if '城镇调查失业率' not in html or '主要指标数据' not in html:
        raise ValueError('不是可识别的国民经济运行报告')
    p = _LeafTables()
    p.feed(html)
    tables = p.tables
    if len(tables) == 4 and tables[0] == tables[2] and (tables[1] == tables[3]):
        tables = tables[:2]
    if len(tables) != 2:
        raise ValueError('上游表格数量或重复结构变化，需检查原文')
    if not any(('环比增速' in c['text'] for c in tables[0][0])) or not any(('同比增长' in c['text'] for c in tables[1][1])):
        raise ValueError('未识别季调环比或主要指标表头')
    output = []
    for i, (name, table, header) in enumerate(zip(('修订后季调月环比', '主要指标'), tables, (1, 2))):
        rows = [r for r in table[header:] if len(r) > 1]
        notes = [r for r in table[header:] if len(r) == 1]
        if keyword and i == 1:
            rows = [r for r in rows if keyword.replace(' ', '') in r[0]['text'].replace(' ', '')]
        output.append({'section': name, 'header_rows': table[:header], 'rows': rows, 'note_rows': notes})
    return {'source_url': url, 'keyword': keyword, 'tables': output, 'note': '主要指标单位按行名与表头读取；调查失业率为百分比，其变化以百分点表示，累计失业率为各月平均。GDP 季度值、累计值、增速的价格口径不同；空值不可当零。关键词只筛主要指标表，季调月环比保留完整。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='command', required=True)
    q = s.add_parser('list')
    q.add_argument('--page', type=int, default=1)
    q = s.add_parser('detail')
    q.add_argument('url')
    q.add_argument('--keyword', default='')
    a = p.parse_args()
    print(json.dumps(macro_report_list(a.page) if a.command == 'list' else macro_report_detail(a.url, a.keyword), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
