"""IMF SDMX 3 named dimensions, codelists and custom series keys."""
import release_runtime
import re
import imf_sdmx_general_adapter as upstream
URN = re.compile('=(?P<agency>[A-Za-z0-9_.-]+):(?P<id>[A-Za-z0-9_.-]+)\\((?P<version>[0-9.+-]+)\\)(?:\\.(?P<concept>[A-Za-z0-9_.-]+))?$')

def _reference(text):
    m = URN.search(text or '')
    if not m:
        raise ValueError('unsupported SDMX reference')
    return m.groupdict()

def _resolve(items, ref):
    matches = [x for x in items if x.get('agencyID') == ref['agency'] and x.get('id') == ref['id']]
    version = ref['version']
    if '+' in version:
        prefix = version.split('+', 1)[0].rstrip('.')
        matches = [x for x in matches if x.get('version', '') == prefix or x.get('version', '').startswith(prefix + '.')]
    else:
        matches = [x for x in matches if x.get('version') == version]
    if not matches:
        return None
    try:
        matches.sort(key=lambda x: tuple((int(y) for y in x['version'].split('.'))), reverse=True)
    except (KeyError, ValueError):
        raise ValueError('unsupported referenced version') from None
    return matches[0]

def _parse(agency, flow):
    result = upstream.structure(agency, flow)
    data = result['sdmx'].get('data', {})
    dsds = data.get('dataStructures', [])
    if len(dsds) != 1:
        raise ValueError('structure does not have exactly one data structure')
    raw = dsds[0].get('dataStructureComponents', {}).get('dimensionList', {}).get('dimensions', [])
    dims = []
    for item in raw:
        ref = _reference(item.get('conceptIdentity'))
        scheme = _resolve(data.get('conceptSchemes', []), ref)
        concept = next((x for x in (scheme or {}).get('concepts', []) if x.get('id') == ref['concept']), None)
        enum = (item.get('localRepresentation') or {}).get('enumeration') or ((concept or {}).get('coreRepresentation') or {}).get('enumeration')
        clref = _reference(enum) if enum else None
        cl = _resolve(data.get('codelists', []), clref) if clref else None
        dims.append({'id': item.get('id'), 'position': item.get('position'), 'name': (concept or {}).get('name'), 'codelist': {'agency': cl.get('agencyID'), 'id': cl.get('id'), 'version': cl.get('version')} if cl else None, 'codes': cl.get('codes') if cl else None})
    if not dims or any((type(x['position']) is not int or not isinstance(x['id'], str) for x in dims)):
        raise ValueError('invalid dimensions')
    dims.sort(key=lambda x: x['position'])
    if [x['position'] for x in dims] != list(range(len(dims))) or len({x['id'] for x in dims}) != len(dims):
        raise ValueError('non-contiguous or duplicate dimensions')
    return (result['source'], dims)

def dimensions(agency, flow):
    source, dims = _parse(agency, flow)
    return {'source': source, 'dimensions': [{k: len(d['codes']) if k == 'code_count' and d['codes'] is not None else None if k == 'code_count' else d.get(k) for k in ('id', 'position', 'name', 'codelist', 'code_count')} for d in dims], 'note': '按 IMF SDMX 序列维度顺序排列；代码结构允许不保证每一组合有观测。查询返回完整时间序列，历史值与预测可能并存。'}

def codes(agency, flow, dimension, keyword='', limit=50, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 100 or type(limit) is not int or (not 1 <= limit <= 500) or (type(offset) is not int) or (offset < 0):
        raise ValueError('invalid code search')
    source, dims = _parse(agency, flow)
    d = next((x for x in dims if x['id'] == dimension), None)
    if d is None or d['codes'] is None:
        raise ValueError('dimension or referenced codelist unavailable')
    rows = [{'code': x.get('id'), 'name': x.get('name'), 'description': x.get('description')} for x in d['codes'] if keyword.casefold() in (str(x.get('id', '')) + ' ' + str(x.get('name', ''))).casefold()]
    return {'source': source, 'dimension': dimension, 'matched': len(rows), 'offset': offset, 'next_offset': offset + limit if offset + limit < len(rows) else None, 'codes': rows[offset:offset + limit], 'note': '只在当前官方结构代码表中匹配；可选代码不保证每个国家或年份有值。'}

def _filter_years(sdmx, start, end):
    data = sdmx.get('data', {})
    structures = data.get('structures')
    datasets = data.get('dataSets')
    if not isinstance(structures, list) or not isinstance(datasets, list):
        raise ValueError('unexpected SDMX data structure for year filtering')
    total = kept = 0
    for ds in datasets:
        idx = ds.get('structure')
        if type(idx) is not int or not 0 <= idx < len(structures) or 'observations' in ds or (not isinstance(ds.get('series'), dict)):
            raise ValueError('unsupported SDMX dataset layout for year filtering')
        obs_dims = structures[idx].get('dimensions', {}).get('observation')
        if not isinstance(obs_dims, list) or len(obs_dims) != 1 or obs_dims[0].get('id') != 'TIME_PERIOD' or (not isinstance(obs_dims[0].get('values'), list)):
            raise ValueError('unsupported SDMX observation dimensions for year filtering')
        times = obs_dims[0]['values']
        for series in ds['series'].values():
            observations = series.get('observations')
            if not isinstance(observations, dict):
                raise ValueError('missing SDMX observations')
            selected = {}
            for k, v in observations.items():
                if not isinstance(k, str) or not k.isdigit() or int(k) >= len(times):
                    raise ValueError('invalid SDMX observation index')
                time = times[int(k)].get('value')
                if not isinstance(time, str) or not re.match('^\\d{4}(?:$|[-A-Z])', time):
                    raise ValueError('unsupported SDMX time code')
                total += 1
                if start <= int(time[:4]) <= end:
                    selected[k] = v
                    kept += 1
            series['observations'] = selected
    return (total, kept)

def query(agency, flow, selections, start=None, end=None):
    if (start is None) != (end is None) or (start is not None and (type(start) is not int or type(end) is not int or (not 1800 <= start <= end <= 2100))):
        raise ValueError('provide valid start and end years together')
    if not isinstance(selections, dict):
        raise ValueError('selections must be a dictionary')
    source, dims = _parse(agency, flow)
    byid = {x['id']: x for x in dims}
    if any((k not in byid for k in selections)):
        raise ValueError('unknown dimension')
    parts = []
    for d in dims:
        val = selections.get(d['id'], '')
        if not isinstance(val, str) or (val and (not re.fullmatch('[A-Za-z0-9_-]+(?:\\+[A-Za-z0-9_-]+)*', val))):
            raise ValueError('invalid code selection')
        if d['codes'] is not None and any((x not in {c.get('id') for c in d['codes']} for x in val.split('+') if x)):
            raise ValueError('unknown code for ' + d['id'])
        parts.append(val)
    key = '.'.join(parts)
    result = upstream.series(agency, flow, key)
    result.update({'structure_source': source, 'dimension_selections': selections, 'sdmx_key': key})
    if start is not None:
        total, kept = _filter_years(result['sdmx'], start, end)
        result['year_filter'] = {'mode': 'local', 'start': start, 'end': end, 'source_observations': total, 'returned_observations': kept}
        result['note'] += ' 本机在完整上游序列返回后按 TIME_PERIOD 年份筛选，保留原索引与属性；并非服务器端过滤。'
    else:
        result['note'] += ' 查询返回完整来源时间序列。'
    result['note'] += ' 模型历史值和预测值混合时须核元数据。'
    return result
