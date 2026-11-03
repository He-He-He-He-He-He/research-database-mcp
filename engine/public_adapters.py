"""公开政策与标准检索：低频只读，使用官方网页自身使用的查询方式。"""
import release_runtime
import argparse, html, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urlencode

class StandardParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.in_table = False
        self.depth = 0
        self.row = None
        self.cell = None
        self.items = []
        self.hcno = None

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == 'table':
            if self.in_table:
                self.depth += 1
            elif 'result_list' in d.get('class', '').split():
                self.in_table = True
                self.depth = 1
        if not self.in_table or self.depth != 1:
            return
        if tag == 'tr':
            self.row = []
            self.hcno = None
        if tag == 'td' and self.row is not None:
            self.cell = []
        if tag in ('a', 'button'):
            m = re.search("showInfo\\('([0-9A-Fa-f]+)'\\)", d.get('onclick', ''))
            if m:
                self.hcno = m.group(1)

    def handle_data(self, s):
        if self.cell is not None:
            self.cell.append(s)

    def handle_endtag(self, tag):
        if not self.in_table:
            return
        if self.depth == 1:
            if tag == 'td' and self.cell is not None:
                self.row.append(' '.join(''.join(self.cell).split()))
                self.cell = None
            if tag == 'tr' and self.row is not None:
                if len(self.row) >= 9 and self.hcno:
                    r = self.row
                    self.items.append({'number': r[1], 'language': r[2], 'adopts_international': r[3], 'name': r[4], 'category': r[5], 'status': r[6], 'published': r[7], 'implemented': r[8], 'id': self.hcno, 'detail_url': 'https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=' + self.hcno})
                self.row = None
        if tag == 'table':
            self.depth -= 1
            if self.depth == 0:
                self.in_table = False

def fetch(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '25', '--user-agent', 'ResearchCatalog/0.1 (personal research)', url], capture_output=True, check=True)
    return p.stdout.decode('utf-8')

def ndrc_search(query, page=1):
    if page < 1 or page > 25:
        raise ValueError('国家发改委页数需在 1–25 之间（网站仅提供最新 500 条）')
    params = {'qt': query, 'tab': 'all', 'page': page, 'pageSize': 20, 'siteCode': 'bm04000fgk', 'key': 'CAB549A94CF659904A7D6B0E8FC8A7E9', 'startDateStr': '', 'endDateStr': '', 'timeOption': 0, 'sort': 'dateDesc'}
    data = json.loads(fetch('https://fwfx.ndrc.gov.cn/api/query?' + urlencode(params)))
    if not data.get('ok') or not isinstance(data.get('data'), dict):
        raise ValueError('政策查询上游未返回成功结果')
    payload = data['data']
    total = payload.get('totalHits')
    rows = payload.get('resultList')
    if total == 0 and 'resultList' not in payload:
        rows = []
    if not isinstance(total, int) or isinstance(total, bool) or total < 0 or (not isinstance(rows, list)):
        raise ValueError('政策查询结果总数或列表无效，不能判定为空结果')
    if len(rows) > 20 or len(rows) > total or (not rows and (page - 1) * 20 < min(total, 500)):
        raise ValueError('政策查询结果总数与页内记录不一致，请稍后核对原站')
    return {'source': '国家发展改革委文件库', 'source_url': 'https://www.ndrc.gov.cn/xxgk/wjk/', 'query': query, 'page': page, 'total_hits': total, 'accessible_limit': 500, 'note': '搜索摘要可能截断或省略发文机关，正式内容和有效性请打开原文核实。', 'items': [{'title': x.get('title'), 'url': x.get('url'), 'date': x.get('docDate'), 'summary': re.sub('<[^>]+>', '', x.get('summary') or '')} for x in rows]}

def standards_search(query, page=1):
    if page < 1:
        raise ValueError('页码需大于 0')
    url = 'https://openstd.samr.gov.cn/bzgk/std/std_list?' + urlencode({'p.p2': query, 'page': page, 'pageSize': 10})
    content = fetch(url)
    p = StandardParser()
    p.feed(content)
    if 'result_list' not in content:
        raise ValueError('国家标准网页结构改变或访问受限，无法解析结果')
    return {'source': '国家标准全文公开系统', 'source_url': 'https://openstd.samr.gov.cn/', 'query': query, 'page': page, 'items': p.items, 'note': '部分标准只公开题录，具体以详情页为准'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='cmd', required=True)
    for cmd in ('ndrc', 'standards'):
        s = sub.add_parser(cmd)
        s.add_argument('keyword')
        s.add_argument('--page', type=int, default=1)
    a = p.parse_args()
    out = ndrc_search(a.keyword, a.page) if a.cmd == 'ndrc' else standards_search(a.keyword, a.page)
    print(json.dumps(out, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或结构变化，不自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
