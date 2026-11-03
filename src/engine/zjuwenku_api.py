"""浙大文库统一检索，返回首页结果及来源类别。"""
import release_runtime
import argparse, json, re
from html.parser import HTMLParser
from urllib.parse import urlencode, urljoin
from urllib.request import urlopen
BASE = 'http://csid.zju.edu.cn/zjuwk/'

class Parser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.items = []
        self.item = None
        self.text = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'a' and re.match('^(?:search/book|award|news|person)/detail\\?', a.get('href', '')):
            self.item = {'text': '', 'url': urljoin(BASE, a['href'])}

    def handle_data(self, data):
        self.text.append(data)
        if self.item is not None:
            self.item['text'] += data

    def handle_endtag(self, tag):
        if tag == 'a' and self.item is not None:
            self.item['text'] = ' '.join(self.item['text'].split())
            self.items.append(self.item)
            self.item = None

def _validate_search_results(total, items):
    if total < 0 or len(items) != min(10, total) or any((not x.get('text') or not x.get('url') for x in items)):
        raise RuntimeError('统一检索总数与首屏题录不一致')

def search(keyword):
    if not keyword.strip():
        raise ValueError('关键词不能为空')
    with urlopen(BASE + 'search?' + urlencode({'keyword': keyword}), timeout=20) as r:
        html = r.read().decode('utf-8')
    p = Parser()
    p.feed(html)
    m = re.search('共\\s*(\\d+)\\s*条记录', ''.join(p.text))
    if not m and '没有相关结果' not in ''.join(p.text):
        raise RuntimeError('未识别结果数，可能服务或页面状态变化')
    total = int(m.group(1)) if m else 0
    _validate_search_results(total, p.items)
    return {'source': '浙大文库', 'query': keyword, 'total': total, 'page': 1, 'items': p.items, 'scope': '统一检索，包含书目作品及文库动态等', 'note': '上游使用未加密 HTTP，请勿提交敏感检索词；分页和详情未验证。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('keyword')
    a = p.parse_args()
    print(json.dumps(search(a.keyword), ensure_ascii=False, indent=2))
