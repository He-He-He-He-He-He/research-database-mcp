"""浙江大学图书馆 OPAC 中文馆藏题名关键词检索首屏。"""
import release_runtime
import argparse, json, re, subprocess
from html.parser import HTMLParser
URL = 'https://opac.zju.edu.cn/F/-'

class Parser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.rows = []
        self.row = None
        self.depth = 0
        self.intitle = False
        self.text = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ('script', 'style'):
            self.skip += 1
        if tag == 'table':
            if self.row is not None:
                self.depth += 1
            elif a.get('class') == 'items':
                self.row = {'title': '', 'description': '', 'id': None}
                self.depth = 1
        if self.row is not None:
            if tag == 'div' and a.get('class') == 'itemtitle':
                self.intitle = True
            if tag == 'a' and re.fullmatch('ZJU(?:01|09)\\d+', a.get('id', '')):
                self.row['id'] = a['id']

    def handle_data(self, data):
        if self.skip:
            return
        self.text.append(data)
        if self.row is not None:
            self.row['description'] += data + ' '
            if self.intitle:
                self.row['title'] += data

    def handle_endtag(self, tag):
        if tag in ('script', 'style') and self.skip:
            self.skip -= 1
        if self.row is None:
            return
        if tag == 'div' and self.intitle:
            self.intitle = False
        if tag == 'table':
            self.depth -= 1
            if self.depth == 0:
                self.row['title'] = ' '.join(self.row['title'].split())
                self.row['description'] = ' '.join(self.row['description'].split())
                if self.row['title']:
                    self.rows.append(self.row)
                self.row = None

def search(keyword, database='chinese'):
    from zju_opac_paged_adapter import search as paged_search
    result = paged_search(keyword, 1, database)
    return {'source': '浙江大学图书馆 OPAC', 'scope': ('中文文献库' if database == 'chinese' else '西文文献库') + '题名关键词，首屏', 'query': keyword, 'items': result['items']}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('keyword')
    p.add_argument('--database', choices=['chinese', 'western'], default='chinese')
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.database), ensure_ascii=False, indent=2))
