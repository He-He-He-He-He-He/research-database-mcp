"""国家知识产权局 2025 年知识产权统计年报部分表格，只读。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
ROOT = 'https://www.cnipa.gov.cn/tjxx/jianbao/year2025/'
CATALOG = {'a1': '分国内外三种专利申请、授权、有效量', 'a6': '分地区分申请人类型国内发明专利申请量', 'b1': '分国内外三种专利授权年度状况', 'c1': '分国内外三种专利有效量', 'e1': '发明及实用新型专利申请按 IPC 部的分类'}

class Tables(HTMLParser):

    def __init__(self):
        super().__init__()
        self.t = None
        self.r = None
        self.c = None
        self.tables = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'table':
            self.t = []
        if tag == 'tr' and self.t is not None:
            self.r = []
        if tag in ('td', 'th') and self.r is not None:
            self.c = {'text': '', 'rowspan': a.get('rowspan', '1'), 'colspan': a.get('colspan', '1')}

    def handle_data(self, s):
        if self.c is not None:
            self.c['text'] += s

    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.c is not None:
            self.c['text'] = ' '.join(self.c['text'].split())
            self.r.append(self.c)
            self.c = None
        if tag == 'tr' and self.r is not None:
            self.t.append(self.r)
            self.r = None
        if tag == 'table' and self.t is not None:
            self.tables.append(self.t)
            self.t = None

def cnipa_stats_list(keyword=''):
    return {'source': '国家知识产权局 2025 年知识产权统计年报', 'scope': '已验证的部分表格目录，非完整年报', 'items': [{'code': k, 'title': v, 'url': ROOT + k[0] + '/' + k + '.html'} for k, v in CATALOG.items() if keyword in v]}

def cnipa_stats_detail(code):
    if code not in CATALOG:
        raise ValueError('仅支持已列出的表格编号')
    url = ROOT + code[0] + '/' + code + '.html'
    p = Tables()
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True)
    if r.returncode:
        raise RuntimeError('上游查询失败（curl 状态 %s）' % r.returncode)
    p.feed(r.stdout.decode('utf-8'))
    table = max(p.tables, key=len, default=[])
    if len(table) < 3:
        raise ValueError('未找到有效统计表')
    return {'source_url': url, 'code': code, 'title': CATALOG[code], 'rows': table, 'xlsx_url': ROOT + code[0] + '/' + code + '.xlsx', 'note': '保留 rowspan 和 colspan；单元格未自动补齐。请核对表头、单位和原表注释；专利有效量与申请授权流量不同。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('code')
    a = p.parse_args()
    print(json.dumps(cnipa_stats_list(a.keyword) if a.cmd == 'list' else cnipa_stats_detail(a.code), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
