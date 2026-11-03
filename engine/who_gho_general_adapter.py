"""WHO 全球卫生观察站 GHO 公开指标目录和观测（本地筛选）。"""
import release_runtime
import argparse
import json
import re
import subprocess
BASE = 'https://ghoapi.azureedge.net/api/'
MAX_BYTES = 15000000

def _get(path):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '35', '--max-filesize', str(MAX_BYTES), BASE + path], capture_output=True, timeout=40)
    if p.returncode:
        raise RuntimeError('WHO GHO 请求失败：' + p.stderr.decode('utf-8', 'replace')[:400])
    if len(p.stdout) > MAX_BYTES:
        raise ValueError('响应超过大小限制')
    v = json.loads(p.stdout)
    if not isinstance(v, dict) or not isinstance(v.get('value'), list):
        raise ValueError('上游返回格式异常')
    if '@odata.nextLink' in v:
        raise ValueError('上游返回分页链接，当前接口未实现后续页')
    return v['value']

def _code(code):
    if not isinstance(code, str) or not re.fullmatch('[A-Za-z0-9_]{1,100}', code):
        raise ValueError('无效指标代码')
    return code

def indicators(keyword='', limit=30):
    if not isinstance(keyword, str) or len(keyword) > 150:
        raise ValueError('关键词无效')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('limit 须为 1–100')
    items = _get('Indicator')
    selected = [x for x in items if keyword.casefold() in (str(x.get('IndicatorCode', '')) + ' ' + str(x.get('IndicatorName', ''))).casefold()]
    return {'source': BASE + 'Indicator', 'total': len(items), 'matched': len(selected), 'items': selected[:limit], 'note': '完整下载官方指标目录并在本地筛选；目录描述不等于完整方法学元数据。'}

def metadata(code):
    code = _code(code)
    match = [r for r in _get('Indicator') if r.get('IndicatorCode') == code]
    if not match:
        raise ValueError('目录中未找到指标代码')
    return {'source': BASE + 'Indicator', 'indicator': match, 'registry': 'https://www.who.int/data/gho/indicator-metadata-registry', 'note': '仅目录级名称；完整定义、方法、单位及适用范围须核对 WHO 指标元数据注册表。'}

def observations(code, country, start=None, end=None, dim1='', limit=100):
    code = _code(code)
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('国家须为大写三字母代码')
    if not isinstance(dim1, str) or not re.fullmatch('[A-Za-z0-9_]{0,80}', dim1):
        raise ValueError('dim1 无效')
    for y in (start, end):
        if y is not None and (isinstance(y, bool) or not isinstance(y, int) or (not 1900 <= y <= 2100)):
            raise ValueError('年份无效')
    if start is not None and end is not None and (start > end):
        raise ValueError('起始年份大于结束年份')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 1000):
        raise ValueError('limit 须为 1–1000')
    items = _get(code)
    matches = []
    for x in items:
        if x.get('SpatialDim') != country or (dim1 and x.get('Dim1') != dim1):
            continue
        year = x.get('TimeDim')
        if start is not None and (not isinstance(year, int) or year < start):
            continue
        if end is not None and (not isinstance(year, int) or year > end):
            continue
        matches.append(x)
    return {'source': BASE + code, 'indicator': code, 'country': country, 'matched': len(matches), 'returned': min(limit, len(matches)), 'items': matches[:limit], 'note': '本机下载该指标的完整响应后筛选国家、时间和维度；上游响应超过 15 MB 将失败，不代表无数据。保留估计值、区间与状态；实际方法以 WHO 元数据为准。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('indicators')
    q.add_argument('keyword', nargs='?', default='')
    q.add_argument('--limit', type=int, default=30)
    q = s.add_parser('metadata')
    q.add_argument('code')
    q = s.add_parser('data')
    q.add_argument('code')
    q.add_argument('country')
    q.add_argument('--start', type=int)
    q.add_argument('--end', type=int)
    q.add_argument('--dim1', default='')
    q.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    v = indicators(a.keyword, a.limit) if a.cmd == 'indicators' else metadata(a.code) if a.cmd == 'metadata' else observations(a.code, a.country, a.start, a.end, a.dim1, a.limit)
    print(json.dumps(v, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
