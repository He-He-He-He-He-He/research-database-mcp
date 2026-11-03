"""UN SDG official geography, disaggregation and paginated observation API."""
import release_runtime
import json, re, requests
BASE = 'https://unstats.un.org/SDGAPI/v1/sdg/Series/'
DOC = 'https://unstats.un.org/SDGAPI/swagger/'

def _code(code):
    if not isinstance(code, str) or not re.fullmatch('[A-Z0-9_]{1,80}', code):
        raise ValueError('指标代码无效')
    return code

def _get(path, params=None):
    with requests.get(BASE + path, params=params, timeout=30, stream=True, allow_redirects=False) as r:
        if r.is_redirect:
            raise RuntimeError('官方接口发生跳转')
        r.raise_for_status()
        b = bytearray()
        for part in r.iter_content(65536):
            b.extend(part)
            if len(b) > 8000000:
                raise ValueError('响应过大，请缩小查询')
        url = r.url
    return (url, json.loads(b))

def dimensions(code):
    code = _code(code)
    url, x = _get(code + '/Dimensions')
    if not isinstance(x, list) or any((not isinstance(v, dict) or not isinstance(v.get('codes'), list) for v in x)):
        raise RuntimeError('维度目录结构异常')
    return {'source_url': url, 'series': code, 'dimensions': x, 'note': '维度代码来自当前官方版本；某代码可选不意味着每个国家年份均有数据。'}

def areas(code, keyword=''):
    code = _code(code)
    if not isinstance(keyword, str) or len(keyword) > 150:
        raise ValueError('地区关键词无效')
    url, x = _get(code + '/GeoAreas')
    if not isinstance(x, list):
        raise RuntimeError('地区目录结构异常')
    found = [i for i in x if isinstance(i, dict) and keyword.casefold() in (str(i.get('geoAreaName', '')) + ' ' + str(i.get('geoAreaCode', ''))).casefold()]
    return {'source_url': url, 'series': code, 'keyword': keyword, 'total': len(x), 'matched': len(found), 'areas': found, 'note': '按本次当前目录本地筛选；地区含国家及区域聚合，不保证各年份均有数据。'}

def observations(code, area, years, filters=None, page=1, page_size=20):
    code = _code(code)
    if isinstance(area, bool) or not isinstance(area, int) or (not 1 <= area <= 999):
        raise ValueError('地区须为 M49 数字代码')
    if not isinstance(years, list) or not 1 <= len(years) <= 30 or any((type(y) is not int or not 1900 <= y <= 2100 for y in years)) or (len(set(years)) != len(years)):
        raise ValueError('须提供 1 至 30 个不同年份')
    if type(page) is not int or not 1 <= page <= 10000 or type(page_size) is not int or (not 1 <= page_size <= 100):
        raise ValueError('分页超限')
    if filters is None:
        filters = {}
    if not isinstance(filters, dict) or len(filters) > 10:
        raise ValueError('维度筛选须为 JSON 对象')
    available = {d['id']: {str(c.get('code')) for c in d['codes']} for d in dimensions(code)['dimensions']}
    selected = []
    for name, vals in filters.items():
        if name not in available or not isinstance(vals, list) or (not 1 <= len(vals) <= 20) or any((not isinstance(v, str) or v not in available[name] for v in vals)) or (len(set(vals)) != len(vals)):
            raise ValueError('筛选维度或代码不在该指标当前目录')
        selected.append({'name': name, 'values': vals})
    params = [('seriesCode', code), ('areaCode', str(area)), ('page', str(page)), ('pageSize', str(page_size))] + [('timePeriod', str(y)) for y in years]
    if selected:
        params.append(('dimensions', json.dumps(selected, ensure_ascii=False, separators=(',', ':'))))
    url, x = _get('Data', params)
    if not isinstance(x, dict) or not isinstance(x.get('data'), list) or x.get('pageNumber') != page:
        raise RuntimeError('观测响应结构或页码异常')
    for r in x['data']:
        if r.get('series') != code or str(r.get('geoAreaCode')) != str(area) or r.get('timePeriodStart') not in years:
            raise RuntimeError('上游返回筛选范围外数据')
        if any((r.get('dimensions', {}).get(k) not in v for k, v in filters.items())):
            raise RuntimeError('上游未遵守维度筛选')
    return {'source_url': url, 'documentation': DOC, 'series': code, 'area': area, 'years': years, 'filters': filters, 'result': x, 'note': '按指定年份逐项传入，避免上游区间参数实测只返回起始年。保留原值、上下界、来源、脚注、维度与属性；页数和排序可能随更新变化。当前发布版可能修订历史数据，不可仅凭观察年份认定当时可得；空结果不是零。'}
