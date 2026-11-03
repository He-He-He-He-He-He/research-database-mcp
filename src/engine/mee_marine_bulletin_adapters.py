"""生态环境部中国海洋及近岸海域环境公报目录查询。"""
import release_runtime
import argparse, html.parser, json, re, subprocess, sys
from urllib.parse import urljoin, urlparse
BASE = 'https://www.mee.gov.cn/hjzl/sthjzk/jagb/'

class Parser(html.parser.HTMLParser):

    def __init__(self):
        super().__init__()
        self.in_li = False
        self.date = False
        self.link = False
        self.href = ''
        self.text = []
        self.datetext = []
        self.rows = []

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'li':
            self.in_li = True
            self.text = []
            self.datetext = []
            self.href = ''
        elif self.in_li and t == 'span' and (a.get('class') == 'date'):
            self.date = True
        elif self.in_li and t == 'a':
            self.link = True
            self.href = a.get('href', '')

    def handle_data(self, x):
        if self.in_li and self.date:
            self.datetext.append(x)
        if self.in_li and self.link:
            self.text.append(x)

    def handle_endtag(self, t):
        if t == 'span':
            self.date = False
        elif t == 'a':
            self.link = False
        elif t == 'li' and self.in_li:
            self.in_li = False
            title = ''.join(self.text).strip()
            day = ''.join(self.datetext).strip()
            url = urljoin(BASE, self.href)
            if re.fullmatch('\\d{4}-\\d{2}-\\d{2}', day) and re.search('^\\d{4}年中国(?:海洋生态环境状况|近岸海域环境质量)公报$', title) and (urlparse(url).hostname == 'www.mee.gov.cn') and url.endswith('.pdf'):
                self.rows.append({'year': int(title[:4]), 'title': title, 'published': day, 'url': url, 'document_type': 'PDF', 'source': '生态环境部'})

def fetch(url):
    p = release_runtime.run(['/usr/bin/curl', '-fsSL', '--max-time', '25', '--user-agent', 'ResearchCatalog/0.1 personal research', url], capture_output=True, check=True)
    return p.stdout.decode('utf-8')

def query(year=None, keyword=''):
    result = []
    for url in (BASE, BASE + 'index_8597_1.shtml'):
        p = Parser()
        p.feed(fetch(url))
        if not p.rows:
            raise RuntimeError('目录网页未返回可解析的公报，可能改版或受限')
        result.extend(p.rows)
    items = [x for x in result if (year is None or x['year'] == year) and keyword in x['title']]
    return {'source_url': BASE, 'scope': '生态环境部目录中可见海洋及近岸海域环境质量公报', 'available_count': len(result), 'items': items, 'note': '仅目录和原始PDF链接；不包含逐页正文或指标数值。2017年及以前与2018年及以后公报名称不同，口径需核对原文。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--year', type=int)
    p.add_argument('--keyword', default='')
    a = p.parse_args()
    print(json.dumps(query(a.year, a.keyword), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
