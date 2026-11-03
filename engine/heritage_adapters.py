"""中国非物质文化遗产网国家级代表性项目查询，只读。"""
import release_runtime
import argparse, json, re, sys
from html.parser import HTMLParser
from research import get, fetch

class Detail(HTMLParser):

    def __init__(self):
        super().__init__()
        self.root = 0
        self.in_text = 0
        self.in_title = False
        self.title = ''
        self.text = []
        self.found = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        c = a.get('class', '').split()
        if not self.root and tag == 'div' and ('inherit_xx1' in c):
            self.root = 1
            self.found = True
            return
        if not self.root:
            return
        if tag == 'div':
            self.root += 1
            if 'text' in c and (not self.in_text):
                self.in_text = self.root
            if 'h30' in c:
                self.in_title = True
        if self.in_text and tag == 'br':
            self.text.append('\n')

    def handle_endtag(self, tag):
        if not self.root:
            return
        if tag == 'div':
            if self.in_text == self.root:
                self.in_text = 0
            if self.in_title:
                self.in_title = False
            self.root -= 1

    def handle_data(self, s):
        if self.in_title:
            self.title += s
        if self.in_text:
            self.text.append(s)

def heritage_search(keyword, page=1):
    if not keyword.strip() or not 1 <= page <= 100:
        raise ValueError('请输入关键词和 1–100 的页码')
    d = get('https://www.ihchina.cn/getProject.html', {'province': '', 'rx_time': '', 'type': '', 'cate': '', 'keywords': keyword, 'category_id': '0', 'limit': '10', 'p': page})
    if 'list' not in d:
        raise ValueError('项目名录响应格式变化')
    return {'source': '中国非物质文化遗产网', 'source_url': 'https://www.ihchina.cn/project.html', 'keyword': keyword, 'page': page, 'total': d.get('total'), 'items': [{'id': x.get('id'), 'title': x.get('title'), 'number': x.get('num'), 'category': x.get('type'), 'batch': re.sub('<[^>]*>', ' ', x.get('rx_time') or ''), 'location': x.get('province'), 'protection_unit': x.get('protect_unit'), 'url': 'https://www.ihchina.cn/project_details/' + str(x.get('id')) + '.html'} for x in d.get('list') or []], 'note': '国家级项目子项，保护信息和名录动态请核对官网。'}

def heritage_detail(id):
    if not re.fullmatch('\\d{1,10}', str(id)):
        raise ValueError('项目 ID 必须是数字')
    url = 'https://www.ihchina.cn/project_details/' + str(id) + '.html'
    p = Detail()
    p.feed(fetch(url))
    if not p.found or not p.title.strip():
        raise ValueError('未找到项目正文，可能页面结构变化')
    return {'source_url': url, 'title': p.title.strip(), 'text': ''.join(p.text).strip()}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('search')
    q.add_argument('keyword')
    q.add_argument('--page', type=int, default=1)
    q = s.add_parser('detail')
    q.add_argument('id')
    a = p.parse_args()
    print(json.dumps(heritage_search(a.keyword, a.page) if a.cmd == 'search' else heritage_detail(a.id), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
