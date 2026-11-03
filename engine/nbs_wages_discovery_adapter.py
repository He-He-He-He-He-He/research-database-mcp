"""Discover and read official NBS wage releases within a bounded catalog range."""
import release_runtime
import re, subprocess
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from moe_education_statistics_adapters import _LeafTables
ROOT = 'https://www.stats.gov.cn/sj/zxfb/'
PATH = re.compile('/sj/zxfb/\\d{6}/t\\d{8}_\\d+\\.html')
TITLE = re.compile('(20\\d{2})年城镇(?:非私营单位|私营单位|单位)就业人员年平均工资(?:情况|\\d+元)')

def _get(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True, timeout=30)
    if p.returncode:
        raise RuntimeError('统计局页面读取失败 curl %s' % p.returncode)
    return p.stdout.decode('utf8')

def catalog(page=1):
    if type(page) is not int or not 1 <= page <= 100:
        raise ValueError('页码须为 1–100')
    url = ROOT if page == 1 else ROOT + f'index_{page - 1}.html'

    class P(HTMLParser):

        def __init__(self):
            super().__init__()
            self.items = {}
            self.official = 0

        def handle_starttag(self, tag, attrs):
            if tag != 'a':
                return
            a = dict(attrs)
            title = a.get('title', '')
            u = urljoin(ROOT, a.get('href', ''))
            x = urlsplit(u)
            if title and x.scheme == 'https' and (x.netloc == 'www.stats.gov.cn') and PATH.fullmatch(x.path):
                self.official += 1
                if TITLE.fullmatch(title):
                    self.items[u] = {'title': title, 'url': u, 'year': int(title[:4])}
    p = P()
    p.feed(_get(url))
    if not p.official:
        raise RuntimeError('未识别统计局发布目录；不能认定为空')
    return {'page': page, 'url': url, 'items': list(p.items.values())}

def detail(url, keyword=''):
    x = urlsplit(url)
    if x.scheme != 'https' or x.netloc != 'www.stats.gov.cn' or x.query or x.fragment or (not PATH.fullmatch(x.path)):
        raise ValueError('仅支持统计局官方发布栏目 URL')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词无效')
    html = _get(url)
    title = TITLE.search(html)
    if not title:
        raise RuntimeError('未识别目标工资报告标题')
    p = _LeafTables()
    p.feed(html)
    tables = p.tables
    if len(tables) % 2 == 0 and tables[:len(tables) // 2] == tables[len(tables) // 2:]:
        tables = tables[:len(tables) // 2]
    if not tables:
        raise RuntimeError('未识别工资报告表格')
    out = []
    needle = ''.join(keyword.split())
    for i, t in enumerate(tables, 1):
        rows = [{'row': j, 'cells': r} for j, r in enumerate(t, 1) if not needle or needle in ''.join((''.join(c['text'].split()) for c in r))]
        out.append({'table': i, 'first_rows': t[:3], 'matched_rows': len(rows), 'rows': rows})
    return {'url': url, 'title': title.group(0), 'year': int(title.group(1)), 'keyword': keyword, 'tables': out, 'note': '逐表匹配，保留原表单元格及前3行供辨认表头；不同年份公报可能拆为私营、非私营等多篇，不应误作完整统计。平均工资不是工资中位数，原文含口径及注释。'}

def find_year(year, keyword='', start_page=1, end_page=20):
    if type(year) is not int or not 2000 <= year <= 2100:
        raise ValueError('年份无效')
    if any((type(x) is not int for x in (start_page, end_page))) or not 1 <= start_page <= end_page <= 100 or end_page - start_page >= 20:
        raise ValueError('最多查询 20 个连续目录页')
    found = []
    visited = []
    seen = set()
    for page in range(start_page, end_page + 1):
        c = catalog(page)
        visited.append(c['url'])
        for item in c['items']:
            if item['year'] == year and item['url'] not in seen:
                seen.add(item['url'])
                found.append(item)
    results = []
    for item in found:
        d = detail(item['url'], keyword)
        if d['year'] != year:
            raise RuntimeError('目录与原文年份不符')
        results.append(d)
    return {'year': year, 'keyword': keyword, 'catalog_urls': visited, 'reports': results, 'note': '仅搜索指定目录页，未找到不代表不存在；多个发布页可能各有不同单位类型；目录动态变化，非历史完整快照。'}
