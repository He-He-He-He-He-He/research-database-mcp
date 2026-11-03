"""Crossref Open Funder Registry search and details."""
import release_runtime
import argparse, json, re, subprocess, sys
from urllib.parse import urlencode
ROOT = 'https://api.crossref.org/funders'

def _get(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True)
    if p.returncode:
        raise RuntimeError(f'Crossref 请求失败 (curl 状态 {p.returncode})')
    d = json.loads(p.stdout)
    if not isinstance(d, dict) or d.get('status') != 'ok' or 'message' not in d:
        raise ValueError('Crossref 响应格式异常')
    return d

def search(query, rows=10, offset=0):
    if not query or not query.strip():
        raise ValueError('资助机构名称不能为空')
    if not 1 <= rows <= 100 or not 0 <= offset <= 100000:
        raise ValueError('分页参数不合法')
    d = _get(ROOT + '?' + urlencode({'query': query, 'rows': rows, 'offset': offset}))
    if not isinstance(d['message'].get('items'), list):
        raise ValueError('未识别机构列表')
    return d

def detail(identifier):
    code = identifier.removeprefix('https://doi.org/10.13039/').removeprefix('10.13039/')
    if not re.fullmatch('\\d{6,15}', code):
        raise ValueError('资助机构编号格式不合法')
    d = _get(ROOT + '/' + code)
    if d['message'].get('id') != code:
        raise ValueError('机构编号与请求不一致')
    return d

def works(identifier, rows=10, *, offset=0):
    code = identifier.removeprefix('https://doi.org/10.13039/').removeprefix('10.13039/')
    if not re.fullmatch('\\d{6,15}', code) or type(rows) is not int or (not 1 <= rows <= 100) or (type(offset) is not int) or (offset < 0) or (offset + rows > 10000):
        raise ValueError('编号、条数或偏移不合法，offset + rows 最多10000')
    d = _get(ROOT + '/' + code + '/works?' + urlencode({'rows': rows, 'offset': offset, 'select': 'DOI,title,type,published,URL'}))
    m = d.get('message')
    if not isinstance(m, dict) or not isinstance(m.get('items'), list) or (not isinstance(m.get('query'), dict)) or (m['query'].get('start-index') != offset) or (len(m['items']) > rows):
        raise ValueError('作品页码或结构异常')
    return {**d, 'toolkit_note': 'Crossref基金方作品元数据不证明全文权限。offset范围最多前10000条；跨请求排序可能变化、结果可能漏重，不能假称全集。'}

def main():
    p = argparse.ArgumentParser(description='Crossref 开放资助机构名录')
    sp = p.add_subparsers(dest='cmd', required=True)
    s = sp.add_parser('search')
    s.add_argument('query')
    s.add_argument('--rows', type=int, default=10)
    s.add_argument('--offset', type=int, default=0)
    d = sp.add_parser('detail')
    d.add_argument('id')
    w = sp.add_parser('works')
    w.add_argument('id')
    w.add_argument('--rows', type=int, default=10)
    w.add_argument('--offset', type=int, default=0)
    a = p.parse_args()
    try:
        print(json.dumps(search(a.query, a.rows, a.offset) if a.cmd == 'search' else detail(a.id) if a.cmd == 'detail' else works(a.id, a.rows, offset=a.offset), ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
if __name__ == '__main__':
    main()
