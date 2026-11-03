"""国家统计局 70 个大中城市商品住宅销售价格指数。"""
import release_runtime
import json, re, subprocess
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from moe_education_statistics_adapters import _LeafTables
REPORTS = {'2025-12': 'https://www.stats.gov.cn/sj/zxfb/202601/t20260119_1962319.html', '2026-08': 'https://www.stats.gov.cn/sj/zxfb/202609/t20260915_1965304.html', '2026-09': 'https://www.stats.gov.cn/sj/zxfb/202610/t20261019_1965609.html'}

def report(period, kind='new', city=''):
    if period not in REPORTS:
        raise ValueError('仅支持已列出的报告期')
    return report_url(REPORTS[period], kind, city)

def report_url(url, kind='new', city=''):
    if kind not in ('new', 'existing'):
        raise ValueError('kind 应为 new 或 existing')
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.netloc != 'www.stats.gov.cn' or parsed.query or parsed.fragment or (not re.fullmatch('/sj/zxfb/\\d{6}/t\\d{8}_\\d+\\.html', parsed.path)):
        raise ValueError('仅支持国家统计局数据发布栏目报告 URL')
    u = url
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', u], capture_output=True, timeout=30)
    if r.returncode:
        raise RuntimeError('国家统计局报告读取失败（curl %s）' % r.returncode)
    html = r.stdout.decode('utf8')
    match = re.search('(20\\d{2})年(\\d{1,2})月份70个大中城市商品住宅销售价格变动情况', html)
    if not match or not 1 <= int(match.group(2)) <= 12:
        raise RuntimeError('报告标题无法核验')
    period = '%s-%02d' % (match.group(1), int(match.group(2)))
    parser = _LeafTables()
    parser.feed(html)
    t = parser.tables
    if len(t) != 12 or any((t[i] != t[i + 6] for i in range(6))):
        raise RuntimeError('未识别两组一致的原表，网页结构可能变化')
    rows = t[0 if kind == 'new' else 1]
    if len(rows) != 37 or not any(('同比' in c['text'] for c in rows[0])):
        raise RuntimeError('未识别价格指数表头')
    width = len(rows[2]) // 2
    if width not in (3, 4):
        raise RuntimeError('未识别城市列数')
    items = []
    for row in rows[2:]:
        if len(row) != width * 2:
            raise RuntimeError('出现非预期的城市行')
        for x in (row[:width], row[width:]):
            name = re.sub('\\s+', '', x[0]['text'])
            values = [c['text'] for c in x[1:]]
            if not name or not all((re.fullmatch('\\d+(?:\\.\\d+)?', v) for v in values)):
                raise RuntimeError('城市或指数值结构变化')
            item = {'city': name, 'month_on_month_index': values[0], 'year_on_year_index': values[1]}
            if width == 4:
                item['year_to_date_index'] = values[2]
            items.append(item)
    if len(items) != 70 or len({x['city'] for x in items}) != 70:
        raise RuntimeError('城市总数或名称不符合预期')
    basis = {'month_on_month_index': '上月=100', 'year_on_year_index': '上年同月=100'}
    if width == 4:
        basis['year_to_date_index'] = '上年同期=100'
    return {'source': '国家统计局70个大中城市商品住宅销售价格指数', 'period': period, 'kind': kind, 'url': u, 'index_basis': basis, 'city': city, 'count': len([x for x in items if city in x['city']]), 'items': [x for x in items if city in x['city']], 'note': '价格指数而非房价金额，原始数值为字符串。1 月原表没有年初至今平均指数；2026年起使用2025年作为新一轮对比基期并调整权数，跨期比较应核对官网统计说明。'}

def periods():
    return [{'period': k, 'url': v} for k, v in REPORTS.items()]

def catalog(page=1):
    if not isinstance(page, int) or isinstance(page, bool) or (not 1 <= page <= 100):
        raise ValueError('目录页码须为 1—100')
    root = 'https://www.stats.gov.cn/sj/zxfb/'
    url = root if page == 1 else root + 'index_%d.html' % (page - 1)
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True, timeout=30)
    if r.returncode:
        raise RuntimeError('国家统计局目录读取失败（curl %s）' % r.returncode)

    class Index(HTMLParser):

        def __init__(self):
            super().__init__()
            self.items = {}
            self.source_items = 0

        def handle_starttag(self, tag, attrs):
            a = dict(attrs)
            title = a.get('title', '')
            u = urljoin(root, a.get('href', ''))
            p = urlsplit(u)
            if tag == 'a' and title and (p.scheme == 'https') and (p.netloc == 'www.stats.gov.cn') and re.fullmatch('/sj/zxfb/\\d{6}/t\\d{8}_\\d+\\.html', p.path):
                self.source_items += 1
            if tag == 'a' and re.fullmatch('20\\d{2}年\\d{1,2}月份70个大中城市商品住宅销售价格变动情况', title) and (p.scheme == 'https') and (p.netloc == 'www.stats.gov.cn') and re.fullmatch('/sj/zxfb/\\d{6}/t\\d{8}_\\d+\\.html', p.path):
                self.items[u] = {'title': title, 'url': u}
    p = Index()
    p.feed(r.stdout.decode('utf8'))
    if not p.source_items:
        raise RuntimeError('未识别统计局发布目录，可能超出页数或网站变化；不能认定无报告')
    return {'source': '国家统计局数据发布栏目', 'page': page, 'url': url, 'items': list(p.items.values()), 'note': '仅筛选指定目录页；该页无结果不代表其他页没有报告。'}

def catalog_search_pages(keyword='', start_page=1, end_page=3):
    if not isinstance(keyword, str):
        raise ValueError('关键词须为字符串')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (start_page, end_page))) or not 1 <= start_page <= end_page <= 100 or end_page - start_page >= 20:
        raise ValueError('起止页须为 1–100 的整数，最多查询连续 20 页')
    items = []
    sources = []
    seen = set()
    for page in range(start_page, end_page + 1):
        result = catalog(page)
        sources.append(result['url'])
        for item in result['items']:
            if item['url'] in seen:
                raise ValueError('跨页出现重复链接，目录可能已更新；请重新查询')
            seen.add(item['url'])
            if keyword in item['title']:
                items.append(item)
    return {'source': '国家统计局数据发布栏目', 'keyword': keyword, 'start_page': start_page, 'end_page': end_page, 'source_urls': sources, 'matched_count': len(items), 'items': items, 'note': '仅筛选指定页标题；目录动态变化，跨页非原子快照，不代表全部历史。报告给出价格指数而非房价金额，基期和口径须核原文。'}

def find_period(period, kind='new', city='', start_page=1, end_page=20):
    """Search bounded official release pages and read the matching report."""
    if not isinstance(period, str) or not re.fullmatch('20\\d{2}-(?:0[1-9]|1[0-2])', period):
        raise ValueError('period 须为 YYYY-MM')
    if kind not in ('new', 'existing') or not isinstance(city, str):
        raise ValueError('kind 或 city 无效')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (start_page, end_page))) or not 1 <= start_page <= end_page <= 100 or end_page - start_page >= 20:
        raise ValueError('起止页须为 1–100 的整数，最多查询连续 20 页')
    year, month = period.split('-')
    title = f'{year}年{int(month)}月份70个大中城市商品住宅销售价格变动情况'
    visited = []
    for page in range(start_page, end_page + 1):
        listing = catalog(page)
        visited.append(listing['url'])
        matches = [item for item in listing['items'] if item['title'] == title]
        if len(matches) > 1:
            raise RuntimeError('同页出现多个匹配报告，请人工核验')
        if matches:
            result = report_url(matches[0]['url'], kind, city)
            if result['period'] != period:
                raise RuntimeError('目录标题与报告期不一致')
            result.update({'catalog_urls': visited, 'catalog_page': page, 'search_scope': '仅检查所列目录页，目录可能变动；未扫描全部历史。'})
            return result
    return {'period': period, 'kind': kind, 'city': city, 'found': False, 'items': [], 'catalog_urls': visited, 'search_scope': '仅检查所列目录页；未找到不能证明报告不存在。'}
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    s.add_parser('periods')
    q = s.add_parser('catalog')
    q.add_argument('--page', type=int, default=1)
    q = s.add_parser('catalog-search-pages')
    q.add_argument('--keyword', default='')
    q.add_argument('--start-page', type=int, default=1)
    q.add_argument('--end-page', type=int, default=3)
    q = s.add_parser('report')
    q.add_argument('period', choices=REPORTS)
    q.add_argument('--kind', choices=['new', 'existing'], default='new')
    q.add_argument('--city', default='')
    q = s.add_parser('url')
    q.add_argument('url')
    q.add_argument('--kind', choices=['new', 'existing'], default='new')
    q.add_argument('--city', default='')
    a = p.parse_args()
    result = periods() if a.cmd == 'periods' else catalog(a.page) if a.cmd == 'catalog' else catalog_search_pages(a.keyword, a.start_page, a.end_page) if a.cmd == 'catalog-search-pages' else report(a.period, a.kind, a.city) if a.cmd == 'report' else report_url(a.url, a.kind, a.city)
    print(json.dumps(result, ensure_ascii=False, indent=2))
