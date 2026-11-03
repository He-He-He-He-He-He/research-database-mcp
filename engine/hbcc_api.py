"""中国历代典籍总目：全文关键词检索的首层来源分组统计。"""
import release_runtime
import argparse
import json
import re
from html.parser import HTMLParser
from urllib.parse import urlencode
from urllib.request import urlopen
BASE = 'http://www.chinabooktrading.com/hbcc/'

class GroupParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.capture = False
        self.value = ''
        self.groups = []
        self.title = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'a' and dict(attrs).get('class') == 'list':
            self.capture = True
            self.value = ''

    def handle_data(self, data):
        if self.capture:
            self.value += data
        self.title += data

    def handle_endtag(self, tag):
        if tag == 'a' and self.capture:
            match = re.fullmatch('\\s*(.*?)\\s*\\(包含\\s*(\\d+)\\s*個子分組\\s*(\\d+)\\s*條書目\\)\\s*', self.value)
            if match:
                self.groups.append({'name': match.group(1), 'subgroups': int(match.group(2)), 'records': int(match.group(3))})
            self.capture = False

def search(keyword):
    if not keyword.strip():
        raise ValueError('关键词不能为空')
    if any((c in keyword for c in '[]!')):
        raise ValueError('关键词包含检索语法特殊字符')
    query = urlencode({'query': f'[ft:{keyword}]!3', 'orderField': 'order0'})
    with urlopen(BASE + 'search/search.action?' + query, timeout=25) as response:
        text = response.read().decode('utf-8')
    p = GroupParser()
    p.feed(text)
    if not p.groups:
        raise RuntimeError('未识别到分组结果；可能无匹配或访问状态、页面结构改变，请到原站确认')
    return {'source': '中国历代典籍总目', 'query': keyword, 'field': '全文关键词', 'result_type': '首层来源分组统计', 'groups': p.groups, 'note': '上游使用未加密 HTTP，请勿提交敏感检索词；逐条题录与全文尚未验证。'}
if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('keyword')
    args = a.parse_args()
    print(json.dumps(search(args.keyword), ensure_ascii=False, indent=2))
