"""国家知识产权局 2025 年知识产权统计年报网页目录与表格。"""
import release_runtime
import json, re, subprocess
from html.parser import HTMLParser
from urllib.parse import urljoin
from cnipa_stats_adapters import Tables
ROOT = 'https://www.cnipa.gov.cn/tjxx/jianbao/year2025/'

def fetch(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True, timeout=30)
    if p.returncode:
        raise RuntimeError('国家知识产权局网页请求失败（curl %s）' % p.returncode)
    return p.stdout.decode('utf-8')

class Links(HTMLParser):

    def __init__(self, pattern):
        super().__init__()
        self.pattern = re.compile(pattern)
        self.href = None
        self.capture = False
        self.text = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'a' and self.pattern.fullmatch(a.get('href', '')):
            self.href = a['href']
            self.text = []
        if self.href and tag == 'div' and (a.get('class') == 'con_right_top'):
            self.capture = True

    def handle_data(self, s):
        if self.capture:
            self.text.append(s)

    def handle_endtag(self, tag):
        if tag == 'div' and self.capture:
            self.capture = False
        if tag == 'a' and self.href:
            title = ' '.join(''.join(self.text).split())
            if title:
                self.links.append((self.href, title))
            self.href = None
            self.capture = False

def catalog(keyword='', group=''):
    top = Links('[a-i]\\.html')
    top.feed(fetch(ROOT + 'indexy.html'))
    if not top.links:
        raise RuntimeError('未找到官方年报目录，页面结构可能变化')
    if group and group not in [x[0][0] for x in top.links]:
        raise ValueError('未知分组，请先查询目录')
    entries = []
    errors = []
    for href, group_title in top.links:
        g = href[0]
        if group and group != g:
            continue
        try:
            listing = Links(g + '/' + g + '\\d+\\.html')
            listing.feed(fetch(urljoin(ROOT, href)))
            if not listing.links:
                raise RuntimeError('分组没有可识别条目')
            for path, title in listing.links:
                if keyword in title:
                    entries.append({'code': path.rsplit('/', 1)[-1][:-5], 'title': title, 'group': g, 'group_title': group_title, 'url': urljoin(ROOT, path)})
        except (RuntimeError, UnicodeError) as exc:
            errors.append({'group': g, 'error': str(exc)})
    return {'source': '国家知识产权局 2025 年知识产权统计年报', 'catalog_url': ROOT + 'indexy.html', 'keyword': keyword, 'group': group or 'all', 'items': entries, 'count': len(entries), 'errors': errors, 'note': '目录按官方页面实时读取；任何分组报错均意味着结果可能不完整。'}

def detail(code):
    if not re.fullmatch('[a-i]\\d+', code):
        raise ValueError('表格编号格式错误')
    listings = catalog(group=code[0])
    match = next((x for x in listings['items'] if x['code'] == code), None)
    if listings['errors']:
        raise RuntimeError('目录读取失败，不能验证该表编号')
    if match is None:
        raise ValueError('该编号不在官方年报目录中')
    parser = Tables()
    parser.feed(fetch(match['url']))
    table = max(parser.tables, key=len, default=[])
    if len(table) < 3:
        raise RuntimeError('未能识别有效表格，请检查官方页面')
    return {'source': '国家知识产权局 2025 年知识产权统计年报', 'code': code, 'title': match['title'], 'url': match['url'], 'rows': table, 'note': '保留合并单元格属性，表头、单位、统计口径、表下注释及数据使用前请核对原网页；此为年报而非实时数据。'}
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('--keyword', default='')
    q.add_argument('--group', default='')
    q = s.add_parser('detail')
    q.add_argument('code')
    a = p.parse_args()
    print(json.dumps(catalog(a.keyword, a.group) if a.cmd == 'list' else detail(a.code), ensure_ascii=False, indent=2))
