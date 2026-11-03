"""浙江大学大型文献信息库丛书及子目检索。"""
import release_runtime
import argparse, json, re
from html.parser import HTMLParser
from urllib.parse import urlencode, urljoin
from urllib.request import urlopen
from bs4 import BeautifulSoup
BASE = 'http://csid.zju.edu.cn/doclib/'

class Parser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.rows = []
        self.row = None
        self.li_depth = 0
        self.capture = None
        self.text = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'li' and a.get('class') == 'rstItem':
            self.row = {'title': '', 'description': '', 'matching_children': [], 'url': None}
            self.li_depth = 1
        elif tag == 'li' and self.row is not None:
            self.li_depth += 1
            self.capture = 'child'
            self.child = ''
        if self.row is not None:
            if tag == 'a' and a.get('href', '').startswith('book?id=') and (not self.row['url']):
                self.row['url'] = urljoin(BASE, a['href'])
            if tag == 'h3':
                self.capture = 'title'
            if tag == 'h4':
                self.capture = 'description'

    def handle_data(self, data):
        self.text.append(data)
        if self.row is not None and self.capture:
            if self.capture == 'child':
                self.child += data
            else:
                self.row[self.capture] += data

    def handle_endtag(self, tag):
        if self.row is None:
            return
        if tag in ('h3', 'h4'):
            self.capture = None
        if tag == 'li':
            if self.li_depth > 1:
                self.row['matching_children'].append(' '.join(self.child.split()))
                self.capture = None
            self.li_depth -= 1
            if self.li_depth == 0:
                self.row['title'] = ' '.join(self.row['title'].split())
                self.row['description'] = ' '.join(self.row['description'].split())
                self.rows.append(self.row)
                self.row = None

def _validate_search_page(html, total, page, items):
    if total == 0:
        if items:
            raise RuntimeError('零结果却解析出题录')
        return
    soup = BeautifulSoup(html, 'html.parser')
    pager = soup.select_one('.m-page')
    m = re.search('(\\d+)\\s*/\\s*(\\d+)\\s*页', pager.get_text(' ', strip=True)) if pager else None
    if not m or int(m.group(1)) != page or int(m.group(2)) != (total + 4) // 5 or (page > int(m.group(2))) or (len(items) != min(5, max(0, total - (page - 1) * 5))):
        raise RuntimeError('搜索页码、总数或解析题录数不一致')

def search(keyword, page=1):
    if not isinstance(keyword, str) or not keyword.strip():
        raise ValueError('关键词不能为空')
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise ValueError('页码须为正整数')
    with urlopen(BASE + 'search?' + urlencode({'query': keyword, 'pageNumber': page, 'pageSize': 5}), timeout=20) as r:
        s = r.read().decode('utf-8')
    p = Parser()
    p.feed(s)
    m = re.search('返回\\s*(\\d+)\\s*个结果', ''.join(p.text))
    if not m and '系统没能为您搜索到与' not in ''.join(p.text):
        raise RuntimeError('未识别结果数，可能服务或页面状态变化')
    total = int(m.group(1)) if m else 0
    _validate_search_page(s, total, page, p.rows)
    return {'source': '浙江大学大型文献信息库', 'query': keyword, 'page': page, 'total': total, 'scope': '丛书与匹配子目；馆方称数据尚不完整', 'items': p.rows, 'note': '上游使用未加密 HTTP，请勿提交敏感检索词；全文未验证。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('keyword')
    p.add_argument('--page', type=int, default=1)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.page), ensure_ascii=False, indent=2))
