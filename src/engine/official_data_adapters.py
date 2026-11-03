"""生态环境部文件库、财政部网站搜索的只读单页解析。"""
import release_runtime
import argparse, json, re, sys
from html.parser import HTMLParser
from urllib.parse import urlencode
from research import fetch

class MeeParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.in_list = False
        self.depth = 0
        self.items = []
        self.field = None
        self.cur = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if not self.in_list and tag == 'div' and (a.get('id') == 'iframe-list'):
            self.in_list = True
            self.depth = 1
            return
        if not self.in_list:
            return
        if tag == 'div':
            self.depth += 1
        if tag == 'td' and 'td-date' in a.get('class', '').split():
            self.cur = {'date': '', 'title': '', 'url': '', 'document_number': ''}
            self.items.append(self.cur)
            self.field = 'date'
        elif tag == 'td' and 'td-right' in a.get('class', '').split():
            self.field = 'document_number'
        elif tag == 'a' and self.cur is not None and a.get('href', '').startswith(('http://www.mee.gov.cn/', 'https://www.mee.gov.cn/')):
            self.cur['url'] = a['href'].split('?')[0]
            self.cur['title'] = a.get('title', '')

    def handle_endtag(self, tag):
        if not self.in_list:
            return
        if tag == 'td':
            self.field = None
        if tag == 'div':
            self.depth -= 1
            if self.depth == 0:
                self.in_list = False

    def handle_data(self, s):
        if self.cur is not None and self.field:
            self.cur[self.field] += s

class MofParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.in_dl = False
        self.inside_dt = False
        self.inside_dd = False
        self.date = False
        self.items = []
        self.cur = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'dl' and (not self.in_dl):
            self.in_dl = True
            self.cur = {'title': '', 'url': '', 'summary': '', 'date': ''}
        if not self.in_dl:
            return
        if tag == 'dt':
            self.inside_dt = True
        if tag == 'dd':
            self.inside_dd = True
        if tag == 'span' and 'fr' in a.get('class', '').split():
            self.date = True
        if tag == 'a' and self.inside_dt and (not self.cur['url']):
            self.cur['url'] = a.get('href', '')

    def handle_endtag(self, tag):
        if not self.in_dl:
            return
        if tag == 'dt':
            self.inside_dt = False
        if tag == 'dd':
            self.inside_dd = False
        if tag == 'span':
            self.date = False
        if tag == 'dl':
            if self.cur['url'] and self.cur['title'].strip():
                self.items.append(self.cur)
            self.in_dl = False

    def handle_data(self, s):
        if not self.in_dl:
            return
        if self.inside_dt:
            self.cur['title'] += s
        elif self.inside_dd:
            self.cur['summary'] += s
        elif self.date:
            self.cur['date'] += s

def clean(items):
    for item in items:
        for k, v in item.items():
            item[k] = ' '.join(v.split()) if isinstance(v, str) else v
    return items

def mee_search(keyword, page=1):
    if not keyword.strip() or not 1 <= page <= 100:
        raise ValueError('请提供关键词和 1–100 的页码')
    url = 'https://www.mee.gov.cn/govsearch/wenjiankujs.jsp?' + urlencode({'Stype': 2, 'type': 1, 'keyword': keyword, 'orderby': 'date', 'page': page})
    source = fetch(url)
    parser = MeeParser()
    parser.feed(source)
    if 'iframe-list' not in source:
        raise ValueError('生态环境部返回非预期页面，无法解析')
    count = re.search('m_nRecordCount\\s*=\\s*(\\d+)', source)
    return {'source': '生态环境部文件库', 'source_url': 'https://www.mee.gov.cn/wjk/', 'keyword': keyword, 'page': page, 'total': int(count.group(1)) if count else None, 'items': clean([x for x in parser.items if x['url'] and x['title']]), 'note': '官网搜索结果包含政策文件和解读，按结果链接核实。'}
MOF_CATEGORIES = {'all': '295890', 'finance-data': '211144', 'policy': '272209', 'interpretation': '277446'}

def mof_search(keyword, page=1, category='all'):
    if not keyword.strip() or not 1 <= page <= 100 or category not in MOF_CATEGORIES:
        raise ValueError('请检查关键词、1–100 的页码和分类')
    url = 'https://search.mof.gov.cn/was5/web/search?' + urlencode({'channelid': MOF_CATEGORIES[category], 'searchword': keyword, 'page': page, 'perpage': 10, 'orderby': '-DOCRELTIME'})
    source = fetch(url)
    parser = MofParser()
    parser.feed(source)
    if 'list_search' not in source:
        raise ValueError('财政部返回非预期页面，无法解析')
    n = re.search('找到相关结果约\\s*(\\d+)\\s*条', source)
    return {'source': '财政部网站', 'source_url': 'https://www.mof.gov.cn/', 'keyword': keyword, 'category': category, 'page': page, 'total': int(n.group(1)) if n else None, 'items': clean(parser.items), 'note': '网站全文检索返回资讯、政策或财政数据文章，不等于结构化财政时间序列。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('mee')
    q.add_argument('keyword')
    q.add_argument('--page', type=int, default=1)
    q = s.add_parser('mof')
    q.add_argument('keyword')
    q.add_argument('--page', type=int, default=1)
    q.add_argument('--category', choices=MOF_CATEGORIES, default='all')
    a = p.parse_args()
    d = mee_search(a.keyword, a.page) if a.cmd == 'mee' else mof_search(a.keyword, a.page, a.category)
    print(json.dumps(d, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
