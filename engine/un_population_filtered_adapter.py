"""UN Population Division Data Portal disaggregation and filtered observations."""
import release_runtime
import un_population_dataportal_adapter as api

def dimensions(indicator):
    if type(indicator) is not int or indicator < 1:
        raise ValueError('指标 ID 须为正整数')
    out = {}
    for name in ('sexes', 'ages', 'categories', 'variants'):
        data, _ = api._get('/metadata/' + name + '/' + str(indicator))
        if not isinstance(data, list) or any((not isinstance(x, dict) or x.get('indicatorId') != indicator for x in data)):
            raise RuntimeError('指标维度元数据异常')
        out[name] = data
    return {'source': api.BASE + '/metadata/{dimension}/' + str(indicator), 'documentation': api.DOCS, 'indicator': indicator, 'dimensions': out, 'note': '当前指标维度代码与年龄区间，不保证任一国家、年份均有记录。年龄 -1 为源接口特殊标记，不能视作负年龄。'}

def data(indicator, location, start, end, sexes=None, variants=None, categories=None, start_age=None, end_age=None, page=1, page_size=50):
    if any((type(x) is not int or x < 1 for x in (indicator, location, page))):
        raise ValueError('指标、地区及页码须为正整数')
    if any((type(x) is not int for x in (start, end))) or not 1900 <= start <= end <= 2100 or type(page_size) is not int or (not 1 <= page_size <= 100):
        raise ValueError('年份或页大小无效')
    meta = dimensions(indicator)['dimensions']
    p = {'pageNumber': page, 'pageSize': page_size}
    checked = {}
    for name, vals, idname in [('sexes', sexes, 'sexId'), ('variants', variants, 'variantId'), ('categories', categories, 'categoryId')]:
        if vals is None:
            continue
        if not isinstance(vals, list) or not 1 <= len(vals) <= 20 or any((type(v) is not int or v < 0 for v in vals)) or (len(vals) != len(set(vals))):
            raise ValueError(name + ' 须为 1–20 个不重复非负整数')
        valid = {x.get(idname) for x in meta[name]}
        if any((v not in valid for v in vals)):
            raise ValueError(name + ' 代码不在指标维度目录')
        p[name] = ','.join(map(str, vals))
        checked[idname] = vals
    for key, val in [('startAge', start_age), ('endAge', end_age)]:
        if val is not None:
            if type(val) is not int or not 0 <= val <= 150:
                raise ValueError('年龄筛选须为 0–150；特殊 -1 暂不支持筛选')
            p[key] = str(val)
    if start_age is not None and end_age is not None and (start_age > end_age):
        raise ValueError('年龄范围无效')
    path = f'/data/indicators/{indicator}/locations/{location}/start/{start}/end/{end}'
    j, defaults = api._get(path, p, auth=True)
    if not isinstance(j, dict) or not isinstance(j.get('data'), list) or j.get('pageNumber') != page:
        raise RuntimeError('人口数据响应或页码异常')
    for r in j['data']:
        if r.get('indicatorId') != indicator or r.get('locationId') != location or any((r.get(k) not in vs for k, vs in checked.items())):
            raise RuntimeError('上游返回不符合指定维度的数据')
        if start_age is not None and (not isinstance(r.get('ageStart'), int) or r['ageStart'] < start_age):
            raise RuntimeError('上游年龄起点不符')
        if end_age is not None and (not isinstance(r.get('ageEnd'), int) or r['ageEnd'] > end_age):
            raise RuntimeError('上游年龄终点不符')
    return {'source': api.BASE + path, 'documentation': api.DOCS, 'request': p, 'indicator': indicator, 'location': location, 'start': start, 'end': end, 'applied_defaults': defaults, 'result': j, 'note': '保留源原始数值、单位/指标定义、source、revision、性别、年龄、estimateType、estimateMethod 和情景。未指定情景时上游可能默认 median 4，见 applied_defaults；模型估计和预测不是普查实测。当前数据可能修订历史值，不能仅凭数据年份推断历史可得；空结果不等于零。'}
