"""国家药监局医疗器械唯一标识数据库：只读查询。"""
import release_runtime
import argparse, json, re, subprocess, sys
from html.parser import HTMLParser
from urllib.parse import urlencode
from research import fetch

class Fields(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.field = None
        self.buf = []
        self.label = None
        self.fields = []
        self.found = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if not self.depth and tag == 'div' and (a.get('class', '').strip() == 'els-table-info'):
            self.depth = 1
            self.found = True
            return
        if not self.depth:
            return
        if tag == 'div':
            self.depth += 1
        if tag in ('th', 'td'):
            self.field = tag
            self.buf = []

    def handle_data(self, s):
        if self.field:
            self.buf.append(s)

    def handle_endtag(self, tag):
        if not self.depth:
            return
        if tag == self.field:
            val = ' '.join(''.join(self.buf).split())
            if tag == 'th':
                self.label = val.rstrip('：:')
            elif self.label is not None:
                self.fields.append({'name': self.label, 'value': val})
                self.label = None
            self.field = None
        if tag == 'div':
            self.depth -= 1

def udi_search(keyword, page=1):
    if not 2 <= len(keyword.strip()) <= 50 or not 1 <= page <= 100:
        raise ValueError('关键词长度应为 2–50，页码 1–100')
    data = urlencode({'query': keyword, 'searchType': 1, 'page': page, 'rows': 15})
    proc = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '25', '--data', data, 'https://udi.nmpa.gov.cn/getDeviceList.html'], capture_output=True, text=True)
    if proc.returncode:
        raise RuntimeError('查询失败（curl 状态 %s）' % proc.returncode)
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise ValueError('国家药监局未返回 JSON')
    if not isinstance(payload.get('rows'), list):
        raise ValueError('响应结构变更')
    return {'source': '国家药监局医疗器械唯一标识数据库', 'source_url': 'https://udi.nmpa.gov.cn/', 'query': keyword, 'page': page, 'total': payload.get('records'), 'items': payload['rows'], 'note': '产品标识信息不代替有效注册证或临床安全性判断。'}

def udi_detail(record_key):
    if not re.fullmatch('[A-Za-z0-9]{8,100}', record_key):
        raise ValueError('记录标识格式不正确')
    url = 'https://udi.nmpa.gov.cn/showDetailCX.html?' + urlencode({'deviceRecordKey': record_key})
    parser = Fields()
    parser.feed(fetch(url))
    if not parser.found or not parser.fields:
        raise ValueError('未识别到产品详情，可能记录无效或页面结构变化')
    return {'source_url': url, 'record_key': record_key, 'fields': parser.fields, 'note': '请核对注册备案状态和最新官方信息。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('search')
    q.add_argument('keyword')
    q.add_argument('--page', type=int, default=1)
    q = s.add_parser('detail')
    q.add_argument('record_key')
    a = p.parse_args()
    print(json.dumps(udi_search(a.keyword, a.page) if a.cmd == 'search' else udi_detail(a.record_key), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
