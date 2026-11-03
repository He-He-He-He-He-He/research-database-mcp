"""杭州市政府公报已验证的经济统计资料。"""
import release_runtime
import argparse, json, subprocess, sys
from html.parser import HTMLParser
CATALOG = {'2026-07': ('2026年7月份杭州市国民经济主要统计资料', 'https://zfgb.hangzhou.gov.cn/136/108220263/t124220263084/530696.shtml'), '2026-08': ('2026年8月份杭州市国民经济主要统计资料', 'https://zfgb.hangzhou.gov.cn/136/109220263/t121220263094/530761.shtml')}

def fetch(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True)
    if p.returncode:
        raise RuntimeError('上游请求失败（curl 状态 %d）' % p.returncode)
    return p.stdout.decode('utf-8')

class Table(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.row = None
        self.cell = None
        self.rows = []
        self.title = ''
        self.source = ''

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t == 'meta' and a.get('name') == 'ArticleTitle':
            self.title = a.get('content', '')
        if t == 'meta' and a.get('name') == 'ContentSource':
            self.source = a.get('content', '')
        if t == 'div':
            if self.depth:
                self.depth += 1
            elif 'html_content' in a.get('class', '').split():
                self.depth = 1
        if self.depth and t == 'tr':
            self.row = []
        if self.depth and self.row is not None and (t in ('td', 'th')):
            self.cell = []

    def handle_data(self, s):
        if self.cell is not None:
            self.cell.append(s)

    def handle_endtag(self, t):
        if self.depth and t in ('td', 'th') and (self.cell is not None):
            self.row.append(' '.join(''.join(self.cell).split()))
            self.cell = None
        if self.depth and t == 'tr' and (self.row is not None):
            self.rows.append(self.row)
            self.row = None
        if t == 'div' and self.depth:
            self.depth -= 1

def hangzhou_economy_list(keyword=''):
    return {'source': '杭州市人民政府公报（杭州市统计局数据）', 'items': [{'id': k, 'title': v[0], 'url': v[1]} for k, v in CATALOG.items() if keyword in k or keyword in v[0]], 'note': '本地精选并验证的两个 2026 年月报，不是官网动态目录或完整历史。'}

def hangzhou_economy_detail(identifier):
    if identifier not in CATALOG:
        raise ValueError('仅支持目录中已验证月份')
    title, url = CATALOG[identifier]
    p = Table()
    p.feed(fetch(url))
    if p.title != title or p.source != '杭州市统计局' or (not p.rows):
        raise ValueError('上游标题、来源或表格异常')
    return {'source': '杭州市人民政府公报（杭州市统计局数据）', 'id': identifier, 'title': title, 'url': url, 'table_rows': p.rows, 'note': '保留官方单元格原始文字；未合并单元格、自动推断同比基期或空值，请核对原文。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('id')
    a = p.parse_args()
    print(json.dumps(hangzhou_economy_list(a.keyword) if a.cmd == 'list' else hangzhou_economy_detail(a.id), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
