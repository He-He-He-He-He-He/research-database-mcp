"""全宋诗分析系统：单次检索题名；当前公开访问为仅含部分诗的试用版。"""
import release_runtime
import argparse
import json
import re
from html.parser import HTMLParser
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen
BASE = 'http://www.chinabooktrading.com/song/'

class Results(HTMLParser):

    def __init__(self):
        super().__init__()
        self.text = []
        self.items = []
        self.link = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'a' and a.get('href', '').startswith('fullText.jsp?'):
            self.link = {'title': '', 'url': urljoin(BASE, a['href'])}

    def handle_data(self, data):
        self.text.append(data)
        if self.link is not None:
            self.link['title'] += data

    def handle_endtag(self, tag):
        if tag == 'a' and self.link is not None:
            self.link['title'] = self.link['title'].strip()
            self.items.append(self.link)
            self.link = None

def search(keyword):
    if not keyword.strip():
        raise ValueError('关键词不能为空')
    data = urlencode({'c': '1', 'b': '1', 'm': keyword, 'i': '', 'h': '', 'j': '0', 'text': keyword}).encode()
    req = Request(urljoin(BASE, 'resultList.jsp'), data=data, headers={'User-Agent': 'Mozilla/5.0'})
    with urlopen(req, timeout=20) as response:
        html = response.read().decode('utf-8')
    parser = Results()
    parser.feed(html)
    match = re.search('共\\s*(\\d+)\\s*條信息', ''.join(parser.text))
    if not match and '沒有符合條件的内容' not in ''.join(parser.text):
        raise RuntimeError('结果页未包含可识别的数量，可能服务或访问状态已改变')
    total = int(match.group(1)) if match else 0
    return {'source': '全宋诗分析系统', 'scope': '试用版本，仅含部分诗', 'query': keyword, 'search_field': '诗内容全文检索', 'total': total, 'items': parser.items, 'note': '上游使用未加密 HTTP，请勿提交敏感检索词；未验证全文和分页。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('keyword')
    args = p.parse_args()
    print(json.dumps(search(args.keyword), ensure_ascii=False, indent=2))
