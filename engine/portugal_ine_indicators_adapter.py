"""Statistics Portugal INE indicator JSON endpoint, constrained dimensions."""
import release_runtime
import argparse, json, re
import requests
URL = 'https://www.ine.pt/ine/json_indicador/pindica.jsp'

def data(indicator, period, geography, dimensions=None, lang='EN', limit=100):
    if not re.fullmatch('\\d{7}', indicator):
        raise ValueError('指标代码须为 7 位数字')
    for x in (period, geography):
        if not isinstance(x, str) or not re.fullmatch('[A-Za-z0-9_-]{1,40}', x):
            raise ValueError('期次与地区须为有效代码')
    if lang not in ('EN', 'PT') or not 1 <= limit <= 200:
        raise ValueError('语言或返回条数无效')
    dims = dimensions or {}
    if not isinstance(dims, dict) or len(dims) > 6:
        raise ValueError('附加维度无效')
    params = {'op': '2', 'varcd': indicator, 'Dim1': period, 'Dim2': geography, 'lang': lang}
    for k, v in dims.items():
        if not re.fullmatch('Dim[3-8]', k) or not isinstance(v, str) or (not re.fullmatch('[A-Za-z0-9_-]{1,40}', v)):
            raise ValueError('附加维度须为 Dim3–Dim8 和安全代码')
        params[k] = v
    s = requests.Session()
    s.trust_env = False
    r = s.get(URL, params=params, timeout=40, stream=True)
    r.raise_for_status()
    parts = []
    size = 0
    for chunk in r.iter_content(65536):
        size += len(chunk)
        if size > 10000000:
            raise ValueError('响应超过 10 MB，请更具体地限定维度')
        parts.append(chunk)
    result = json.loads(b''.join(parts))
    if not isinstance(result, list) or len(result) != 1 or (not isinstance(result[0], dict)):
        raise ValueError('官方响应结构异常')
    info = result[0]
    if info.get('IndicadorCod') != indicator or not isinstance(info.get('Dados'), dict):
        raise ValueError('官方未返回期望指标数据，请检查代码')
    rows = []
    total = 0
    for year, items in info['Dados'].items():
        if not isinstance(items, list):
            raise ValueError('官方观测格式异常')
        for item in items:
            if not isinstance(item, dict):
                raise ValueError('官方观测格式异常')
            total += 1
            if len(rows) < limit:
                rows.append({'period': year, **item})
    return {'source': r.url, 'indicator': {k: v for k, v in info.items() if k != 'Dados'}, 'total_returned_by_source': total, 'shown': len(rows), 'rows': rows, 'note': '结果附带指标标题、元数据链接、维度与原始值；本地限量但不代表上游分页。期次和地区须依该指标维度定义输入；不同指标的 Dim2 不一定是地理。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('indicator')
    p.add_argument('period')
    p.add_argument('geography')
    p.add_argument('--dimensions', default='{}')
    p.add_argument('--lang', choices=['EN', 'PT'], default='EN')
    p.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    print(json.dumps(data(a.indicator, a.period, a.geography, json.loads(a.dimensions), a.lang, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
