"""全国标准信息公共服务平台地方标准，只读单页检索。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urlencode
from research import fetch
BASE = 'https://dbba.sacinfo.org.cn/'

class Detail(HTMLParser):

    def __init__(self):
        super().__init__()
        self.in_head = False
        self.in_title = False
        self.title = ''
        self.part = None
        self.buf = []
        self.name = None
        self.fields = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        c = a.get('class', '').split()
        if tag == 'div' and 'page-header' in c:
            self.in_head = True
        if tag == 'h4' and self.in_head:
            self.in_title = True
        if tag in ('dt', 'dd') and 'basicInfo-item' in c:
            self.part = tag
            self.buf = []

    def handle_data(self, s):
        if self.in_title:
            self.title += s
        if self.part:
            self.buf.append(s)

    def handle_endtag(self, tag):
        if tag == 'h4':
            self.in_title = False
        if tag == 'div' and self.in_head:
            self.in_head = False
        if self.part == tag:
            value = ' '.join(''.join(self.buf).split())
            if tag == 'dt':
                self.name = value
            elif self.name:
                self.fields.append({'name': self.name, 'value': value})
                self.name = None
            self.part = None

def local_standard_search(keyword, page=1, status='现行'):
    if not keyword.strip() or not 1 <= page <= 100 or status not in ('现行', '有更新版', '废止', ''):
        raise ValueError('请检查关键词、页码、标准状态')
    data = urlencode({'current': page, 'size': 10, 'key': keyword, 'ministry': '', 'industry': '', 'pubdate': '', 'date': '', 'status': status})
    proc = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '25', '--data', data, BASE + 'stdQueryList'], capture_output=True, text=True)
    if proc.returncode:
        raise RuntimeError('请求失败（curl 状态 %s）' % proc.returncode)
    try:
        d = json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise ValueError('上游未返回 JSON')
    if not isinstance(d.get('records'), list):
        raise ValueError('结果结构变化')
    rows = []
    for x in d['records']:
        x = dict(x)
        pk = x.get('pk', '')
        if re.fullmatch('[0-9a-fA-F]{64}', pk):
            x['detail_url'] = BASE + 'stdDetail/' + pk
        rows.append(x)
    return {'source': '全国标准信息公共服务平台地方标准', 'source_url': BASE + 'stdList', 'keyword': keyword, 'status': status, 'page': page, 'total': d.get('total'), 'items': rows, 'note': '地方标准题录；时间字段为毫秒时间戳。全文和现行状态以官网为准。'}

def local_standard_detail(pk):
    if not re.fullmatch('[0-9a-fA-F]{64}', pk):
        raise ValueError('标准 ID 必须为 64 位十六进制')
    u = BASE + 'stdDetail/' + pk
    p = Detail()
    p.feed(fetch(u))
    if not p.title or not p.fields:
        raise ValueError('没有识别到详情，可能网页改版或记录不存在')
    return {'source_url': u, 'title': p.title.strip(), 'fields': p.fields, 'note': '仅基础信息；请在原站核查标准状态和完整内容。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('search')
    q.add_argument('keyword')
    q.add_argument('--page', type=int, default=1)
    q.add_argument('--status', choices=['现行', '有更新版', '废止', '全部'], default='现行')
    q = s.add_parser('detail')
    q.add_argument('id')
    a = p.parse_args()
    print(json.dumps(local_standard_search(a.keyword, a.page, '' if a.status == '全部' else a.status) if a.cmd == 'search' else local_standard_detail(a.id), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
