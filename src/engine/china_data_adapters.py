"""国家数据关键词与国务院政策文件库，只读单页查询。"""
import release_runtime
import argparse, html, json, re, sys
from research import get, fetch
from html.parser import HTMLParser
from urllib.parse import urlsplit
CATEGORIES = {'gongwen': '国务院文件', 'bumenfile': '部门文件', 'otherfile': '政策解读', 'gongbao': '国务院公报'}

def stats_search(keyword, page=1, size=5):
    if not keyword.strip() or not 1 <= page <= 1000 or (not 1 <= size <= 20):
        raise ValueError('请提供关键词、1–1000 的页码和 1–20 的每页数量')
    data = get('https://data.stats.gov.cn/dg/website/publicrelease/web/external/query', {'search': keyword, 'pagenum': page, 'pageSize': size})
    if not data.get('success') or not isinstance(data.get('data'), dict):
        raise ValueError('国家数据查询没有返回成功结果')
    return data

def policy_search(keyword, page=1, size=10, category='gongwen', field='title'):
    if not keyword.strip() or not 1 <= page <= 100 or (not 1 <= size <= 20) or (category not in CATEGORIES) or (field not in ('title', 'content')):
        raise ValueError('请检查关键词、页码、每页数量、分类及检索范围')
    params = {'t': 'zhengcelibrary', 'q': keyword, 'searchfield': field, 'sort': 'pubtime', 'sortType': '1', 'p': page, 'n': size, 'type': 'gwyzcwjk', 'childtype': category}
    d = get('https://sousuo.www.gov.cn/search-gov/data', params)
    if d.get('code') != 200 or not isinstance(d.get('searchVO'), dict):
        raise ValueError('国务院政策文件库没有返回成功结果')
    data = (d['searchVO'].get('catMap') or {}).get(category)
    if not isinstance(data, dict):
        raise ValueError('响应未包含目标分类，可能改版')

    def clean(s):
        return html.unescape(re.sub('<[^>]*>', '', s or ''))
    return {'source': '国务院政策文件库', 'source_url': 'https://sousuo.www.gov.cn/zcwjk/', 'query': keyword, 'search_field': field, 'category': category, 'category_name': CATEGORIES[category], 'page': page, 'page_size': size, 'total': data.get('totalCount'), 'items': [{'id': x.get('id'), 'title': clean(x.get('title')), 'url': x.get('url'), 'date': x.get('pubtimeStr'), 'document_number': x.get('pcode'), 'issuer': x.get('puborg'), 'summary': clean(x.get('summary'))} for x in data.get('listVO') or []], 'note': '结果来自所选分类；文件效力以官方正文及后续文件为准'}

class PolicyContent(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.found = False
        self.text = []

    def handle_starttag(self, tag, attrs):
        if not self.depth and tag == 'div' and (dict(attrs).get('id') == 'UCAP-CONTENT'):
            self.depth = 1
            self.found = True
            return
        if self.depth and tag == 'div':
            self.depth += 1
        if self.depth and tag in ('br', 'p'):
            self.text.append('\n')

    def handle_endtag(self, tag):
        if self.depth and tag == 'div':
            self.depth -= 1
        if self.depth and tag == 'p':
            self.text.append('\n')

    def handle_data(self, data):
        if self.depth:
            self.text.append(data)

def policy_detail(url):
    parts = urlsplit(url)
    if parts.scheme != 'https' or parts.netloc != 'www.gov.cn' or (not re.fullmatch('/zhengce/zhengceku/\\d{6}/content_\\d+\\.htm', parts.path)) or parts.query or parts.fragment:
        raise ValueError('只接受中国政府网政策文件库正文链接（https://www.gov.cn/zhengce/zhengceku/YYYYMM/content_数字.htm）')
    parser = PolicyContent()
    parser.feed(fetch(url))
    if not parser.found:
        raise ValueError('未识别到官方正文区域，可能是网页模板改变')
    return {'source_url': url, 'text': ''.join(parser.text).strip(), 'note': '页面正文；文件效力请核对后续文件与官网信息。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='cmd', required=True)
    q = sub.add_parser('stats-search')
    q.add_argument('keyword')
    q.add_argument('--page', type=int, default=1)
    q.add_argument('--size', type=int, default=5)
    q = sub.add_parser('gov-policy')
    q.add_argument('keyword')
    q.add_argument('--page', type=int, default=1)
    q.add_argument('--size', type=int, default=10)
    q.add_argument('--category', choices=list(CATEGORIES), default='gongwen')
    q.add_argument('--field', choices=['title', 'content'], default='title')
    q = sub.add_parser('gov-detail')
    q.add_argument('url')
    a = p.parse_args()
    if a.cmd == 'stats-search':
        d = stats_search(a.keyword, a.page, a.size)
    elif a.cmd == 'gov-policy':
        d = policy_search(a.keyword, a.page, a.size, a.category, a.field)
    else:
        d = policy_detail(a.url)
    print(json.dumps(d, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或接口变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
