"""ROR v2 research-organization search and record retrieval."""
import release_runtime
import argparse, json, re, subprocess, sys
from urllib.parse import urlencode
ROOT = 'https://api.ror.org/v2/organizations'

def _get(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True)
    if p.returncode:
        raise RuntimeError(f'ROR 请求失败 (curl 状态 {p.returncode})')
    data = json.loads(p.stdout)
    if not isinstance(data, dict):
        raise ValueError('ROR 响应格式异常')
    return data

def search(query, page=1):
    if not query or not query.strip():
        raise ValueError('机构名称不能为空')
    if not 1 <= page <= 1000:
        raise ValueError('页码应在 1–1000 之间')
    data = _get(ROOT + '?' + urlencode({'query': query, 'page': page}))
    if not isinstance(data.get('items'), list):
        raise ValueError('未识别 ROR 查询结果')
    return data

def detail(identifier):
    code = identifier.removeprefix('https://ror.org/').removeprefix('ror.org/')
    if not re.fullmatch('0[a-hj-km-np-tv-z0-9]{6}[0-9]{2}', code):
        raise ValueError('ROR ID 格式不合法')
    data = _get(ROOT + '/' + code)
    if data.get('id') != 'https://ror.org/' + code:
        raise ValueError('ROR 返回的 ID 与请求不一致')
    return data

def main():
    p = argparse.ArgumentParser(description='ROR 研究机构注册信息')
    sub = p.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('search')
    s.add_argument('query')
    s.add_argument('--page', type=int, default=1)
    d = sub.add_parser('detail')
    d.add_argument('id')
    a = p.parse_args()
    try:
        print(json.dumps(search(a.query, a.page) if a.cmd == 'search' else detail(a.id), ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
if __name__ == '__main__':
    main()
