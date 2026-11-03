"""气象科学专业知识服务系统数据集目录和元数据；不下载观测数据。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urlencode
from research import fetch

class Meta(HTMLParser):

    def __init__(self):
        super().__init__()
        self.in_li = False
        self.li_class = []
        self.buf = []
        self.pending = None
        self.fields = []
        self.in_title = False
        self.title = ''

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        c = a.get('class', '').split()
        if tag == 'h2' and 'search-term' in c:
            self.in_title = True
        if tag == 'li' and ('title' in c or 'words' in c):
            self.in_li = True
            self.li_class = c
            self.buf = []

    def handle_endtag(self, tag):
        if tag == 'h2':
            self.in_title = False
        if tag == 'li' and self.in_li:
            v = ' '.join(''.join(self.buf).split())
            if 'title' in self.li_class:
                self.pending = v
            elif self.pending is not None:
                self.fields.append({'name': self.pending, 'value': v})
                self.pending = None
            self.in_li = False

    def handle_data(self, s):
        if self.in_title:
            self.title += s
        if self.in_li:
            self.buf.append(s)

def cma_search(keyword, category='102'):
    if not keyword.strip() or not re.fullmatch('\\d{1,5}', str(category)):
        raise ValueError('请输入关键词和数字类型的数据分类编号')
    args = ['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '25', '--data', urlencode({'subjectIDs': '', 'CategoryID': category, 'keyWord': keyword}), 'https://k.data.cma.cn/mekb/?r=data/classifySearch']
    result = release_runtime.run(args, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError('查询失败（curl 状态 %s）' % result.returncode)
    try:
        rows = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise ValueError('上游未返回 JSON')
    if not isinstance(rows, list):
        raise ValueError('上游数据结构变化')
    return {'source': '气象科学专业知识服务系统', 'category': category, 'keyword': keyword, 'items': [{'code': x.get('DataCode'), 'name': x.get('CHNName'), 'detail_url': 'https://k.data.cma.cn/mekb/?' + urlencode({'r': 'data/detail', 'dataCode': x.get('DataCode', '')})} for x in rows], 'note': '数据集目录，数据下载和共享权限以详情页为准；个别条目链接可能失效。'}

def cma_detail(code):
    if not re.fullmatch('[A-Za-z0-9._-]{1,80}', code):
        raise ValueError('数据代码格式错误')
    url = 'https://k.data.cma.cn/mekb/?' + urlencode({'dataCode': code, 'r': 'data/detail'})
    parser = Meta()
    parser.feed(fetch(url))
    if not parser.title.strip() or not parser.fields:
        raise ValueError('未找到有效详情，可能是失效条目')
    return {'source_url': url, 'code': code, 'title': ' '.join(parser.title.split()).lstrip('◎ '), 'metadata': parser.fields, 'note': '仅元数据；共享条件和实际申请以网站当前说明为准。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='cmd', required=True)
    q = sub.add_parser('search')
    q.add_argument('keyword')
    q.add_argument('--category', default='102')
    q = sub.add_parser('detail')
    q.add_argument('code')
    a = p.parse_args()
    print(json.dumps(cma_search(a.keyword, a.category) if a.cmd == 'search' else cma_detail(a.code), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
