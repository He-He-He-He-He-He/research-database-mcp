"""国家外汇管理局人民币汇率中间价表，只读。"""
import release_runtime
import argparse, datetime, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urlencode
URL = 'https://www.safe.gov.cn/AppStructured/hlw/RMBQuery.do'

class Rates(HTMLParser):

    def __init__(self):
        super().__init__()
        self.table = False
        self.cell = None
        self.row = None
        self.rows = []

    def handle_starttag(self, tag, attrs):
        if tag == 'table' and dict(attrs).get('id') == 'InfoTable':
            self.table = True
        elif self.table and tag == 'tr':
            self.row = []
        elif self.table and self.row is not None and (tag in ('td', 'th')):
            self.cell = []

    def handle_data(self, text):
        if self.cell is not None:
            self.cell.append(text)

    def handle_endtag(self, tag):
        if self.table and tag in ('td', 'th') and (self.cell is not None):
            self.row.append(' '.join(''.join(self.cell).split()))
            self.cell = None
        elif self.table and tag == 'tr' and (self.row is not None):
            if self.row:
                self.rows.append(self.row)
            self.row = None
        elif self.table and tag == 'table':
            self.table = False

def safe_rates(start='', end=''):
    if bool(start) != bool(end):
        raise ValueError('开始和结束日期须同时提供')
    args = ['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25']
    if start:
        try:
            a = datetime.date.fromisoformat(start)
            b = datetime.date.fromisoformat(end)
        except ValueError:
            raise ValueError('日期须为 YYYY-MM-DD')
        if a.isoformat() != start or b.isoformat() != end or a > b:
            raise ValueError('日期格式错误或开始晚于结束')
        args += ['--data', urlencode({'startDate': start, 'endDate': end, 'queryYN': 'true'})]
    p = release_runtime.run(args + [URL], capture_output=True)
    if p.returncode:
        raise RuntimeError('上游请求失败（curl 状态 %d）' % p.returncode)
    parser = Rates()
    parser.feed(p.stdout.decode('utf-8'))
    if not parser.rows or parser.rows[0][0] != '日期':
        raise ValueError('未识别官方汇率表')
    headers = parser.rows[0]
    items = []
    for row in parser.rows[1:]:
        if len(row) != len(headers) or not re.fullmatch('\\d{4}-\\d{2}-\\d{2}', row[0]):
            raise ValueError('汇率表格式变化')
        items.append({'date': row[0], 'quotes': dict(zip(headers[1:], row[1:]))})
    return {'source': '国家外汇管理局人民币汇率中间价', 'source_url': URL, 'start': start or None, 'end': end or None, 'items': items, 'note': '保留原表文字数值；不同币种的报价方向和单位可能不同，请以官方说明为准。单次查询可能仅显示前 10 行；长区间请分段查询。'}

def safe_rate_detail(date):
    result = safe_rates(date, date)
    if not result['items']:
        return {'source': result['source'], 'source_url': URL, 'date': date, 'quote': None, 'note': '上游该日期没有记录；不推断原因。'}
    if len(result['items']) != 1 or result['items'][0]['date'] != date:
        raise ValueError('上游返回日期不匹配')
    return {'source': result['source'], 'source_url': URL, **result['items'][0], 'note': result['note']}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('--start', default='')
    q.add_argument('--end', default='')
    q = s.add_parser('detail')
    q.add_argument('date')
    a = p.parse_args()
    print(json.dumps(safe_rates(a.start, a.end) if a.cmd == 'list' else safe_rate_detail(a.date), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
