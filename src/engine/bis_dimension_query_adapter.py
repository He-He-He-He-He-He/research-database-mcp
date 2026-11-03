"""BIS SDMX dimension and code discovery with explicit bounded queries."""
import release_runtime
import re
import bis_general_adapter as base

def _structure(flow, version='latest'):
    doc = base.structure(flow, version)
    if not isinstance(doc, dict) or not isinstance(doc.get('data'), dict):
        raise RuntimeError('BIS structure unavailable')
    d = doc['data']
    flows = [x for x in d.get('dataflows', []) if x.get('id') == flow]
    if len(flows) != 1:
        raise RuntimeError('BIS dataflow missing or ambiguous')
    ref = flows[0].get('structure', '')
    m = re.search('=([^:]+):([^()]+)\\(([^)]+)\\)$', ref)
    if not m:
        raise RuntimeError('BIS structure reference unrecognized')
    agency, ident, ver = m.groups()
    structures = [x for x in d.get('dataStructures', []) if x.get('id') == ident and x.get('agencyID') == agency and (x.get('version') == ver)]
    if len(structures) != 1:
        raise RuntimeError('BIS structure missing or ambiguous')
    dimensions = structures[0].get('dataStructureComponents', {}).get('dimensionList', {}).get('dimensions', [])
    if not isinstance(dimensions, list) or not dimensions or any((type(x.get('position')) is not int or not isinstance(x.get('id'), str) for x in dimensions)):
        raise RuntimeError('BIS dimensions unrecognized')
    dimensions = sorted(dimensions, key=lambda x: x['position'])
    if len({x['id'] for x in dimensions}) != len(dimensions) or len({x['position'] for x in dimensions}) != len(dimensions):
        raise RuntimeError('BIS dimensions ambiguous')
    return (d, dimensions)

def _codes(d, dimension):
    ref = dimension.get('localRepresentation', {}).get('enumeration', '')
    m = re.search('=([^:]+):([^()]+)\\(([^)]+)\\)$', ref)
    if not m:
        raise ValueError('dimension has no explicit code list in source structure')
    agency, ident, ver = m.groups()
    found = [x for x in d.get('codelists', []) if x.get('id') == ident and x.get('agencyID') == agency and (x.get('version') == ver)]
    if len(found) != 1 or not isinstance(found[0].get('codes'), list):
        raise RuntimeError('BIS code list missing or ambiguous')
    return found[0]['codes']

def dimensions(flow, version='latest'):
    d, dims = _structure(flow, version)
    result = []
    for x in dims:
        try:
            count = len(_codes(d, x))
        except (ValueError, RuntimeError):
            count = None
        result.append({'id': x['id'], 'position': x['position'], 'code_count': count, 'representation': x.get('localRepresentation')})
    return {'source': base.BASE, 'flow': flow, 'version_requested': version, 'dimensions': result, 'note': '仅列序列维度，时间通过查询起止参数指定；代码列表不保证每个组合有数据。'}

def codes(flow, dimension, keyword='', limit=50, offset=0, version='latest'):
    if not isinstance(keyword, str) or len(keyword) > 120 or type(limit) is not int or (not 1 <= limit <= 100) or (type(offset) is not int) or (offset < 0):
        raise ValueError('invalid filter or pagination')
    d, dims = _structure(flow, version)
    found = [x for x in dims if x['id'] == dimension]
    if len(found) != 1:
        raise ValueError('unknown dimension')
    values = _codes(d, found[0])
    q = keyword.strip().casefold()
    rows = [{'id': x.get('id'), 'name': x.get('name')} for x in values if isinstance(x, dict) and (not q or q in (str(x.get('id', '')) + ' ' + str(x.get('name', ''))).casefold())]
    return {'source': base.BASE, 'flow': flow, 'dimension': dimension, 'keyword': keyword, 'total_matches': len(rows), 'offset': offset, 'limit': limit, 'items': rows[offset:offset + limit], 'note': '仅对本次来源结构返回的代码列表本地筛选和分页；列表可能不完整，代码有效不保证有观测。'}

def query(flow, selections, start, end, version='latest'):
    if not isinstance(selections, dict) or not selections:
        raise ValueError('selections must be a nonempty mapping')
    d, dims = _structure(flow, version)
    ids = [x['id'] for x in dims]
    if set(selections) != set(ids):
        raise ValueError('provide a value list for each sequence dimension: ' + ','.join(ids))
    parts = []
    combinations = 1
    for x in dims:
        values = selections[x['id']]
        if not isinstance(values, list) or not 1 <= len(values) <= 10 or any((not isinstance(v, str) or not re.fullmatch('[A-Za-z0-9_-]{1,80}', v) for v in values)):
            raise ValueError('invalid dimension values')
        valid = {z.get('id') for z in _codes(d, x) if isinstance(z, dict)}
        if not set(values) <= valid:
            raise ValueError('code not present in returned list for ' + x['id'])
        combinations *= len(set(values))
        if combinations > 100:
            raise ValueError('too many dimension combinations; narrow the selection')
        parts.append('+'.join(values))
    key = '.'.join(parts)
    result = base.series(flow, key, start, end, version)
    unverified = set()
    for dataset in result.get('datasets', []):
        for series in dataset.get('series', []):
            attrs = {**dataset.get('attributes', {}), **series.get('attributes', {})}
            for name, values in selections.items():
                if name not in attrs:
                    unverified.add(name)
                elif attrs[name] not in values:
                    raise RuntimeError('BIS returned a series outside requested dimension: ' + name)
    result.update({'flow': flow, 'selection': selections, 'key': key, 'unverified_dimensions': sorted(unverified), 'note': '按官方维度顺序和代码查询；缺少回显的维度列在 unverified_dimensions。保留来源状态属性，单位及预测或修订口径须核对原始结构，时间范围由源站执行。'})
    return result
