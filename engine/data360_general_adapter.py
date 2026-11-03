"""World Bank Data360 通用指标目录和多国、多个数据集的单指标观测查询。"""
import release_runtime
import argparse, json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://data360api.worldbank.org/data360/'

def _token(v, name, maxlen=100):
    if not isinstance(v, str) or not re.fullmatch('[A-Za-z0-9_.-]{1,' + str(maxlen) + '}', v):
        raise ValueError(name + ' 格式无效')
    return v

def _get(path, params):
    url = BASE + path + '?' + urlencode(params)
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '30', url], capture_output=True, text=True, timeout=35)
    if p.returncode:
        raise RuntimeError('Data360 请求失败')
    return (url, json.loads(p.stdout))

def indicators(dataset, keyword='', limit=100, *, offset=0):
    _token(dataset, 'dataset')
    if not isinstance(keyword, str) or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 1000) or (type(offset) is not int) or (not 0 <= offset <= 100000):
        raise ValueError('keyword、limit 或 offset 无效')
    url, data = _get('indicators', {'datasetId': dataset})
    if not isinstance(data, list) or any((not isinstance(x, str) for x in data)):
        raise RuntimeError('Data360 目录结构变更')
    found = sorted((x for x in data if keyword.casefold() in x.casefold()))
    return {'source': 'World Bank Data360 indicator directory', 'source_url': url, 'dataset': dataset, 'matching': len(found), 'offset': offset, 'limit': limit, 'next_offset': offset + limit if offset + limit < len(found) else None, 'indicators': found[offset:offset + limit], 'scope': '每次重新获取来源列表，按指标ID排序并本地截取（与旧版源顺序不同）；源端未提供独立总量，目录更新仍可能导致跨请求遗漏或重复；官方目录只返回指标 ID，不包含标题；可查看每个指标 metadata_url 模板 https://data360files.worldbank.org/data360-data/metadata/{dataset}/{indicator}.pdf，文件可用性依指标而异。'}

def series(dataset, indicator, country, start, end):
    _token(dataset, 'dataset')
    _token(indicator, 'indicator')
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country 须为大写 ISO3')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1900 <= start <= end <= 2100:
        raise ValueError('年份范围无效')
    url, data = _get('data', {'DATABASE_ID': dataset, 'INDICATOR': indicator, 'REF_AREA': country, 'timePeriodFrom': start, 'timePeriodTo': end})
    rows = data.get('value') if isinstance(data, dict) else None
    if not isinstance(rows, list) or not isinstance(data.get('count'), int) or data['count'] != len(rows):
        raise RuntimeError('Data360 数据不完整或响应结构异常')
    if any((r.get('DATABASE_ID') != dataset or r.get('INDICATOR') != indicator or r.get('REF_AREA') != country for r in rows)):
        raise RuntimeError('Data360 响应维度不匹配')
    return {'source': 'World Bank Data360 API', 'source_url': url, 'metadata_url': 'https://data360files.worldbank.org/data360-data/metadata/' + dataset + '/' + indicator + '.pdf', 'dataset': dataset, 'indicator': indicator, 'country': country, 'scope': '保留本次响应的原始观测及维度，较大结果的分页和完整性尚未单独验证；同一年可能有多种单位、性别、频率、统计或其他分组，必须逐条核对维度、UNIT_MULT 和元数据，不可直接合并。各源覆盖、估计与预测口径不同，元数据文件可能不可用；空结果不是零。', 'count': len(rows), 'data': rows}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    a = s.add_parser('indicators')
    a.add_argument('dataset')
    a.add_argument('--keyword', default='')
    a.add_argument('--limit', type=int, default=100)
    a.add_argument('--offset', type=int, default=0)
    b = s.add_parser('series')
    b.add_argument('dataset')
    b.add_argument('indicator')
    b.add_argument('country')
    b.add_argument('start', type=int)
    b.add_argument('end', type=int)
    x = p.parse_args()
    v = indicators(x.dataset, x.keyword, x.limit, offset=x.offset) if x.cmd == 'indicators' else series(x.dataset, x.indicator, x.country, x.start, x.end)
    print(json.dumps(v, ensure_ascii=False, indent=2))
