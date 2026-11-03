"""Czech Statistical Office DataStat dataset catalogue, dimensions, and single observation."""
import release_runtime
import argparse, json, re
from urllib.parse import quote
import requests
BASE = 'https://data.csu.gov.cz/api/'

def _code(value):
    if not isinstance(value, str) or not re.fullmatch('[A-Za-z0-9_.-]{1,80}', value):
        raise ValueError('代码无效')
    return quote(value, safe='')

def _get(path, params=None):
    s = requests.Session()
    s.trust_env = False
    r = s.get(BASE + path, params=params, timeout=30, stream=True)
    r.raise_for_status()
    parts = []
    n = 0
    for c in r.iter_content(65536):
        n += len(c)
        if n > 10000000:
            raise ValueError('响应超 10 MB')
        parts.append(c)
    return (r.url, json.loads(b''.join(parts)))

def search(query, limit=30):
    if not isinstance(query, str) or not query.strip() or len(query) > 120 or (not 1 <= limit <= 100):
        raise ValueError('关键词或条数无效')
    url, j = _get('katalog/v1/sady')
    if not isinstance(j, list):
        raise ValueError('目录结构异常')
    rows = [x for x in j if query.casefold() in json.dumps(x, ensure_ascii=False).casefold()]
    return {'source': url, 'total': len(rows), 'datasets': rows[:limit], 'note': '关键词在完整目录的本地文本中匹配；捷克语名称通常更易命中。'}

def metadata(dataset):
    url, j = _get('katalog/v1/sady/' + _code(dataset))
    if not isinstance(j, dict) or j.get('kod') != dataset:
        raise ValueError('元数据不匹配')
    return {'source': url, 'metadata': j}

def dimension(code):
    url, j = _get('katalog/v1/dimenze/' + _code(code) + '/polozky')
    if not isinstance(j, (list, dict)):
        raise ValueError('维度响应异常')
    return {'source': url, 'dimension': code, 'values': j, 'note': '不同维度可能有大量条目，需根据数据集版本核对。'}

def observation(dataset, indicator, version, dimensions):
    _code(dataset)
    _code(indicator)
    _code(version)
    if not isinstance(dimensions, dict) or not 1 <= len(dimensions) <= 8:
        raise ValueError('请提供 1–8 个维度及选项')
    for k, v in dimensions.items():
        _code(k)
        _code(v)
    url, j = _get('dotaz/v1/data/sady/' + _code(dataset) + '/hodnoty/' + _code(indicator), {'verze': version, 'kodyDimenzi': ','.join(dimensions), 'kodyPolozek': ','.join(dimensions.values())})
    if not isinstance(j, dict) or 'ukazatel' not in j or 'dimenze' not in j:
        raise ValueError('观测响应异常')
    return {'source': url, 'dataset': dataset, 'version': version, 'observation': j, 'note': '保留上游指标定义、计量单位、各维度及状态；统计对象与地区、时间、是否初步须核对官方元数据。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('search')
    q.add_argument('query')
    q.add_argument('--limit', type=int, default=30)
    q = s.add_parser('metadata')
    q.add_argument('dataset')
    q = s.add_parser('dimension')
    q.add_argument('code')
    q = s.add_parser('value')
    q.add_argument('dataset')
    q.add_argument('indicator')
    q.add_argument('version')
    q.add_argument('--dimensions', required=True)
    a = p.parse_args()
    v = search(a.query, a.limit) if a.cmd == 'search' else metadata(a.dataset) if a.cmd == 'metadata' else dimension(a.code) if a.cmd == 'dimension' else observation(a.dataset, a.indicator, a.version, json.loads(a.dimensions))
    print(json.dumps(v, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
