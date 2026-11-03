"""哈萨克斯坦国家统计局 Taldau 公开指标检索、元数据和时间序列。"""
import release_runtime
import argparse
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://taldau.stat.gov.kz/en/Api/'
MAX_BYTES = 10000000

def _digits(value, name):
    text = str(value)
    if isinstance(value, bool) or not re.fullmatch('[0-9]{1,12}', text):
        raise ValueError(name + ' 须为数字代码')
    return text

def _get(path, params=None):
    url = BASE + path + ('?' + urlencode(params) if params else '')
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', str(MAX_BYTES), url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('Taldau 请求失败：' + p.stderr.decode('utf-8', 'replace')[:400])
    if len(p.stdout) > MAX_BYTES:
        raise ValueError('响应过大')
    return (url, json.loads(p.stdout))

def search(keyword, limit=30):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 150:
        raise ValueError('请输入关键词')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('limit 须为 1–100')
    url, value = _get('Search', {'keyword': keyword.strip()})
    if not isinstance(value, dict) or not isinstance(value.get('results'), list):
        raise ValueError('搜索返回结构异常')
    return {'source': url, 'total': value.get('total'), 'returned': min(len(value['results']), limit), 'items': value['results'][:limit], 'note': '最多返回指定条数；此限制在本地执行，不保证上游完整分页。'}

def metadata(indicator, period=7, measure=1, measure_kfc=1):
    ident = _digits(indicator, '指标')
    period = _digits(period, '周期')
    measure = _digits(measure, '计量单位')
    if isinstance(measure_kfc, bool) or not isinstance(measure_kfc, (int, float)) or (not 0 < measure_kfc <= 1000000000000.0):
        raise ValueError('单位换算系数无效')
    url, value = _get('GetIndexAttributes', {'periodId': period, 'measureID': measure, 'measureKFC': measure_kfc, 'indexId': ident})
    if not isinstance(value, dict) or str(value.get('id')) != ident:
        raise ValueError('指标元数据格式或编号异常')
    return {'source': url, 'metadata': value, 'note': '单位与倍率由查询参数和上游定义共同决定；须核对默认单位、统计频率、口径和原始指标页。'}

def data(indicator, period=7, dictionaries=None, region='', start=None, end=None):
    ident = _digits(indicator, '指标')
    period = _digits(period, '周期')
    if not isinstance(dictionaries, list) or not dictionaries or len(dictionaries) > 4:
        raise ValueError('须指定 1–4 个字典代码')
    dics = [_digits(x, '字典') for x in dictionaries]
    if len(dics) != len(set(dics)):
        raise ValueError('字典代码重复')
    if not isinstance(region, str) or len(region) > 150:
        raise ValueError('地区关键词无效')
    for year in (start, end):
        if year is not None and (isinstance(year, bool) or not isinstance(year, int) or (not 1800 <= year <= 2100)):
            raise ValueError('年份无效')
    if start is not None and end is not None and (start > end):
        raise ValueError('起始年份不能大于结束年份')
    url, value = _get('GetIndexData/' + ident, {'period': period, 'dics': ','.join(dics)})
    if not isinstance(value, list):
        raise ValueError('统计数据返回结构异常')
    rows = []
    for row in value:
        if not isinstance(row, dict) or not isinstance(row.get('periods'), list):
            raise ValueError('时间序列结构异常')
        if region and (not any((region.casefold() in str(x).casefold() for x in row.get('termNames', [])))):
            continue
        row = dict(row)
        if start is not None or end is not None:
            filtered = []
            for obs in row['periods']:
                m = re.fullmatch('\\d{2}\\.\\d{2}\\.(\\d{4})', str(obs.get('date', '')))
                if not m:
                    filtered.append(obs)
                    continue
                year = int(m.group(1))
                if (start is None or year >= start) and (end is None or year <= end):
                    filtered.append(obs)
            row['periods'] = filtered
        rows.append(row)
    return {'source': url, 'indicator': ident, 'period': period, 'dictionaries': dics, 'rows': rows, 'note': '地区和年份在本地筛选；返回原始值字符串及日期，未知日期格式保留。字典、单位与周期须核对对应官方元数据；数据会修订。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('search')
    q.add_argument('keyword')
    q.add_argument('--limit', type=int, default=30)
    q = s.add_parser('metadata')
    q.add_argument('indicator')
    q.add_argument('--period', type=int, default=7)
    q.add_argument('--measure', type=int, default=1)
    q.add_argument('--measure-kfc', type=float, default=1)
    q = s.add_parser('data')
    q.add_argument('indicator')
    q.add_argument('--period', type=int, default=7)
    q.add_argument('--dictionaries', required=True)
    q.add_argument('--region', default='')
    q.add_argument('--start', type=int)
    q.add_argument('--end', type=int)
    a = p.parse_args()
    v = search(a.keyword, a.limit) if a.cmd == 'search' else metadata(a.indicator, a.period, a.measure, a.measure_kfc) if a.cmd == 'metadata' else data(a.indicator, a.period, a.dictionaries.split(','), a.region, a.start, a.end)
    print(json.dumps(v, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
