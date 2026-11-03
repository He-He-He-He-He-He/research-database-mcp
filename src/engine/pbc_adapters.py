"""中国人民银行官网搜索：只读，单次一页。"""
import release_runtime
import argparse, json, re, sys
from html.parser import HTMLParser
from urllib.parse import urlencode
from research import fetch

class SearchParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.item = None
        self.items = []
        self.header = False
        self.summary = False
        self.dates = False
        self.date_span = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = a.get('class', '').split()
        if tag == 'div' and 'searchMod' in classes and (not self.depth):
            self.depth = 1
            self.item = {'title': '', 'url': '', 'summary': '', 'date': ''}
            return
        if not self.depth:
            return
        if tag == 'div':
            self.depth += 1
        if tag == 'h3':
            self.header = True
        if tag == 'a' and self.header and (not self.item['url']):
            self.item['url'] = a.get('href', '')
        if tag == 'p' and 'txtCon' in classes:
            self.summary = True
        if tag == 'p' and 'dates' in classes:
            self.dates = True
        if tag == 'span' and self.dates and ('date_' not in classes):
            self.date_span = True

    def handle_endtag(self, tag):
        if not self.depth:
            return
        if tag == 'h3':
            self.header = False
        if tag == 'span':
            self.date_span = False
        if tag == 'p':
            self.summary = False
            self.dates = False
        if tag == 'div':
            self.depth -= 1
            if self.depth == 0 and self.item['url'] and self.item['title'].strip():
                self.items.append({k: ' '.join(v.split()) for k, v in self.item.items()})
                self.item = None

    def handle_data(self, data):
        if not self.depth:
            return
        if self.header:
            self.item['title'] += data
        elif self.summary:
            self.item['summary'] += data
        elif self.date_span:
            self.item['date'] += data

def pbc_search(keyword, page=1, sort='relevance'):
    if not keyword.strip() or not 1 <= page <= 100 or sort not in ('relevance', 'date'):
        raise ValueError('请检查关键词、页码和排序')
    params = {'pageId': 'c177a85bd02b4114bebebd210809f691', 'q': keyword, 'pNo': page, 'sr': 'score desc' if sort == 'relevance' else 'dateTime desc'}
    source = fetch('https://wzdig.pbc.gov.cn/search/pcRender?' + urlencode(params))
    p = SearchParser()
    p.feed(source)
    if 'default-result-list' not in source and 'result-count' not in source:
        raise ValueError('中国人民银行返回非预期页面')
    n = re.search('class="result-count">\\s*(\\d+)\\s*条结果', source)
    return {'source': '中国人民银行网站搜索', 'source_url': 'https://www.pbc.gov.cn/', 'keyword': keyword, 'page': page, 'sort': sort, 'total': int(n.group(1)) if n else None, 'items': p.items, 'note': '返回央行及分支网站的公开文档；请核对发布机关和生效时间。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('keyword')
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--sort', choices=['relevance', 'date'], default='relevance')
    a = p.parse_args()
    print(json.dumps(pbc_search(a.keyword, a.page, a.sort), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或页面结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
