"""World Bank Indicators API: country lookup, indicator metadata and series."""
import release_runtime
import argparse, json, re, subprocess, sys
from urllib.parse import urlencode
ROOT = 'https://api.worldbank.org/v2'

def _get(path, params=None):
    args = {'format': 'json', **(params or {})}
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', ROOT + path + '?' + urlencode(args)], capture_output=True)
    if p.returncode:
        raise RuntimeError(f'世界银行请求失败 (curl 状态 {p.returncode})')
    data = json.loads(p.stdout)
    if isinstance(data, list) and len(data) == 1 and isinstance(data[0], dict) and isinstance(data[0].get('message'), list):
        messages = data[0]['message']
        detail = '; '.join((str(item.get('value') or item.get('key') or 'unknown error') for item in messages if isinstance(item, dict)))
        raise ValueError('世界银行 API 错误：' + (detail or '未知错误'))
    if not isinstance(data, list) or len(data) != 2 or (not isinstance(data[0], dict)):
        raise ValueError('世界银行响应错误或格式变化')
    if not isinstance(data[1], list):
        raise ValueError('未找到数据')
    return data

def countries(query):
    if not query or not query.strip():
        raise ValueError('国家或地区关键词不能为空')
    meta, rows = _get('/country', {'per_page': 400})
    if meta.get('pages', 1) > 1:
        raise ValueError('国家目录超过单页，需更新实现')
    q = query.casefold().strip()
    hits = [x for x in rows if q in x.get('name', '').casefold() or q == x.get('id', '').casefold() or q == x.get('iso2Code', '').casefold()]
    return {'query': query, 'matches': len(hits), 'items': hits}

def indicator(code):
    if not re.fullmatch('[A-Za-z0-9_.-]{1,64}', code):
        raise ValueError('指标代码格式不合法')
    data = _get('/indicator/' + code)
    if not data[1]:
        raise ValueError('未找到指标')
    return data

def series(country, code, start, end):
    if not re.fullmatch('[A-Za-z]{2,3}', country):
        raise ValueError('国家代码应为 2 或 3 个字母')
    if not re.fullmatch('[A-Za-z0-9_.-]{1,64}', code):
        raise ValueError('指标代码格式不合法')
    if not 1900 <= start <= end <= 2100:
        raise ValueError('年份范围不合法')
    return _get('/country/' + country + '/indicator/' + code, {'date': f'{start}:{end}', 'per_page': 250})

def main():
    p = argparse.ArgumentParser(description='世界银行公开指标数据')
    sp = p.add_subparsers(dest='cmd', required=True)
    s = sp.add_parser('countries')
    s.add_argument('query')
    d = sp.add_parser('indicator')
    d.add_argument('code')
    v = sp.add_parser('series')
    v.add_argument('country')
    v.add_argument('code')
    v.add_argument('--start', type=int, required=True)
    v.add_argument('--end', type=int, required=True)
    a = p.parse_args()
    try:
        result = countries(a.query) if a.cmd == 'countries' else indicator(a.code) if a.cmd == 'indicator' else series(a.country, a.code, a.start, a.end)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
if __name__ == '__main__':
    main()
