"""国家统计局 70 城住宅销售价格指数，读取发布目录及原网页表格。"""
import release_runtime
import argparse
import json
import re
import subprocess
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from moe_education_statistics_adapters import _LeafTables
ROOT = 'https://www.stats.gov.cn'
INDEX = ROOT + '/sj/zxfb/'
PATH = re.compile('/sj/zxfb/\\d{6}/t\\d{8}_\\d+\\.html')

def _get(url):
    result = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True, check=True)
    return result.stdout.decode('utf-8')

class _Index(HTMLParser):

    def __init__(self):
        super().__init__()
        self.items = {}
        self.release_urls = set()

    def handle_starttag(self, tag, attrs):
        if tag != 'a':
            return
        d = dict(attrs)
        name = d.get('title', '')
        url = urljoin(INDEX, d.get('href', ''))
        u = urlsplit(url)
        if name and u.scheme == 'https' and (u.netloc == 'www.stats.gov.cn') and PATH.fullmatch(u.path):
            self.release_urls.add(url)
        if '70个大中城市商品住宅销售价格变动情况' in name and u.scheme == 'https' and (u.netloc == 'www.stats.gov.cn') and PATH.fullmatch(u.path):
            self.items[url] = {'title': name, 'url': url}

def housing_list():
    for page in range(1, 6):
        url = INDEX if page == 1 else INDEX + f'index_{page - 1}.html'
        parser = _Index()
        parser.feed(_get(url))
        if not parser.release_urls:
            raise ValueError('第 %d 页未识别官方发布目录，无法确认检索结果' % page)
        items = list(parser.items.values())
        if items:
            return {'source_url': url, 'source_page': page, 'items': items, 'note': '按顺序检查最新发布目录，返回第一个匹配页；并非全部历史报告。'}
    return {'source_url': INDEX, 'source_page': None, 'items': [], 'note': '仅检查最新发布目录前 5 页，未找到匹配报告；不能据此认定全部历史无报告。'}

def housing_detail(url, city=''):
    u = urlsplit(url)
    if u.scheme != 'https' or u.netloc != 'www.stats.gov.cn' or u.query or u.fragment or (not PATH.fullmatch(u.path)):
        raise ValueError('仅支持统计局最新发布栏目的官方详情 URL')
    if len(city) > 40:
        raise ValueError('城市名过长')
    html = _get(url)
    if '70个大中城市' not in html or '住宅销售价格' not in html:
        raise ValueError('不是可识别的 70 城住宅价格报告')
    parser = _LeafTables()
    parser.feed(html)
    raw = parser.tables
    if len(raw) == 12 and all((raw[i] == raw[i + 6] for i in range(6))):
        raw = raw[:6]
    if len(raw) != 6:
        raise ValueError('上游表格数量或移动端重复结构变化，请检查原网页')
    names = ['新建商品住宅指数', '二手住宅指数', '新建分类面积：第一组城市', '新建分类面积：第二组城市', '二手分类面积：第一组城市', '二手分类面积：第二组城市']
    tables = []
    needle = ''.join(city.split())
    for i, (name, table) in enumerate(zip(names, raw)):
        headers = 2 if i < 2 else 3
        if len(table) <= headers or '城市' not in ''.join((c['text'] for c in table[0])):
            raise ValueError('表头格式变化')
        rows = table[headers:]
        if needle:
            rows = [row for row in rows if any((needle in ''.join(row[j]['text'].split()) for j in ([0, 4] if i < 2 and len(row) > 4 else [0]) if j < len(row)))]
        tables.append({'section': name, 'header_rows': table[:headers], 'rows': rows})
    return {'source_url': url, 'city_filter': city, 'tables': tables, 'note': '保留原始表格单元格及合并属性；表 1、2 同行包含两个城市。环比上月=100、同比上年同月=100，并非百分比涨幅，也不是房价绝对值。城市筛选为本地逐行匹配，须按表头识别两侧城市。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    s.add_parser('list')
    d = s.add_parser('detail')
    d.add_argument('url')
    d.add_argument('--city', default='')
    a = p.parse_args()
    print(json.dumps(housing_list() if a.cmd == 'list' else housing_detail(a.url, a.city), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
