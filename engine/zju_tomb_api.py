"""浙江大学中国历代墓志数据库题名检索，首屏结果。"""
import release_runtime
import argparse, json, re
from html.parser import HTMLParser
from urllib.parse import urlencode, urljoin
from urllib.request import urlopen
BASE = 'http://csid.zju.edu.cn/tomb/'
LIBS = ['歷代墓誌', '館藏拓片', '中國宗教', '名家書法', '鴛鴦墓誌', '女性墓誌', '石刻美術']

class Parser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.rows = []
        self.row = None
        self.cell = None
        self.text = []

    def unknown_decl(self, data):
        pass

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'tr' and a.get('class') == 'bline':
            m = re.search("open\\('([^']+)'", a.get('onclick', ''))
            self.row = {'cells': [], 'url': urljoin(BASE, m.group(1)) if m else None}
        elif tag == 'td' and self.row is not None:
            self.cell = ''

    def handle_data(self, data):
        self.text.append(data)
        if self.cell is not None:
            self.cell += data

    def handle_endtag(self, tag):
        if tag == 'td' and self.row is not None and (self.cell is not None):
            self.row['cells'].append(' '.join(self.cell.split()))
            self.cell = None
        if tag == 'tr' and self.row is not None:
            if len(self.row['cells']) == 6:
                c = self.row['cells']
                self.rows.append(dict(zip(['number', 'title', 'dynasty', 'date', 'type', 'reference'], c)) | {'url': self.row['url']})
            self.row = None

def _validate_first_page(total, rows):
    if total < 0 or len(rows) != min(15, total):
        raise RuntimeError('墓志结果总数与解析条数不一致')

def search(keyword):
    if not keyword.strip():
        raise ValueError('关键词不能为空')
    pairs = [('tag', '3'), ('smSearchSelect', 'title'), ('smSearType', '0'), ('smInputText', keyword)] + [('subLibType', x) for x in LIBS]
    with urlopen(BASE + 'stone/list?' + urlencode(pairs), timeout=20) as r:
        html = r.read().decode('utf-8')
    p = Parser()
    p.feed(html)
    m = re.search('記錄數\\s*:\\s*(\\d+)', ''.join(p.text))
    if not m and '未找到任何数据' not in ''.join(p.text):
        raise RuntimeError('未识别结果数，可能服务或页面状态变化')
    total = int(m.group(1)) if m else 0
    _validate_first_page(total, p.rows)
    return {'source': '中国历代墓志数据库', 'query': keyword, 'field': '题名，建议繁体字', 'total': total, 'page': 1, 'items': p.rows, 'note': '上游使用未加密 HTTP，请勿提交敏感检索词；分页、详情和图像权限未验证。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('keyword')
    a = p.parse_args()
    print(json.dumps(search(a.keyword), ensure_ascii=False, indent=2))
