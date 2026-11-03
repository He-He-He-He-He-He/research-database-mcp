"""宿州市公共数据开放平台数据服务目录，只查询公开接口元数据。"""
import release_runtime
import json, re, subprocess
from html.parser import HTMLParser
from urllib.parse import urlencode
BASE = 'https://www.ahsz.gov.cn'

def fetch(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True, timeout=30)
    if p.returncode:
        raise RuntimeError('宿州市数据开放平台请求失败（curl %s）' % p.returncode)
    return p.stdout.decode('utf-8')

class CatalogParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.count = None
        self.names = []
        self.ids = []
        self.page = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id') == 'record_count':
            self.count = a.get('count')
        if a.get('id') == 'page_num':
            self.page = a.get('value')
        if tag == 'input' and a.get('name') == 'servicesidinput':
            self.ids.append(a.get('value', ''))
        if tag == 'input' and a.get('name') == 'servicesnameinput':
            self.names.append(a.get('value', ''))

class DetailParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.stack = []
        self.buf = []
        self.kind = None
        self.depth = 0
        self.result = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = a.get('class', '').split()
        if self.kind:
            self.depth += 1
            return
        if tag == 'h4':
            self.kind = 'title'
        elif tag == 'li' and any((x in classes for x in ['serviceapply'])):
            return
        elif tag == 'div' and 'explain-information' in classes:
            self.kind = 'description'
        elif tag == 'li' and self.stack and ('list-inline' in self.stack[-1]):
            self.kind = 'field'
        if self.kind:
            self.depth = 1
            self.buf = []
        elif tag == 'ul':
            self.stack.append(classes)

    def handle_data(self, s):
        if self.kind:
            self.buf.append(s)

    def handle_endtag(self, tag):
        if self.kind:
            self.depth -= 1
            if self.depth == 0:
                value = ' '.join(''.join(self.buf).split())
                if value:
                    self.result.append((self.kind, value))
                self.kind = None
        elif tag == 'ul' and self.stack:
            self.stack.pop()

def search(keyword='', page=1):
    if not 1 <= int(page) <= 10000:
        raise ValueError('页码须为正整数')
    url = BASE + '/oportal/api/index?' + urlencode({'q': keyword, 'page': int(page)})
    p = CatalogParser()
    p.feed(fetch(url))
    if p.count is None or not str(p.count).replace(',', '').isdigit() or len(p.ids) != len(p.names) or any((not re.fullmatch('[0-9a-f]{32}', i) for i in p.ids)):
        raise RuntimeError('未识别接口目录，页面结构可能改变')
    if p.page is None or str(p.page) != str(int(page) - 1):
        raise RuntimeError('服务器未返回请求页')
    return {'source': '宿州市公共数据开放平台数据服务目录', 'keyword': keyword, 'page': int(page), 'total': int(p.count.replace(',', '')), 'items': [{'id': i, 'title': n, 'url': BASE + '/oportal/api/' + i + '/detail'} for i, n in zip(p.ids, p.names)], 'note': '仅目录元数据；接口数据调用可能需要登录、申请和签名，不能据目录推断数据可用。'}

def detail(identifier):
    if not re.fullmatch('[0-9a-f]{32}', identifier):
        raise ValueError('服务 ID 格式错误')
    url = BASE + '/oportal/api/' + identifier + '/detail'
    p = DetailParser()
    p.feed(fetch(url))
    titles = [v for k, v in p.result if k == 'title']
    descriptions = [v for k, v in p.result if k == 'description']
    fields = [v for k, v in p.result if k == 'field' and any((v.startswith(x) for x in ('来源部门：', '领域：', '发布时间：', '更新时间：', '开放类型：')))]
    if not titles or not descriptions:
        raise RuntimeError('未识别服务详情，可能站点结构变化')
    return {'source': '宿州市公共数据开放平台数据服务目录', 'id': identifier, 'url': url, 'title': titles[0], 'fields': fields, 'descriptions': descriptions, 'note': '仅显示公开接口说明；具体使用许可与授权条件以官网为准，未申请或调用数据接口。'}
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    x = s.add_parser('search')
    x.add_argument('keyword', nargs='?', default='')
    x.add_argument('--page', type=int, default=1)
    x = s.add_parser('detail')
    x.add_argument('id')
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.page) if a.cmd == 'search' else detail(a.id), ensure_ascii=False, indent=2))
