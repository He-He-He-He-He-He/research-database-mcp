"""ILOSTAT named dimension discovery and custom data selection."""
import release_runtime
import re, xml.etree.ElementTree as ET
import ilostat_general_adapter as upstream

def _local(x):
    return x.tag.rsplit('}', 1)[-1]

def _name(x):
    n = [y.text or '' for y in x if _local(y) == 'Name' and y.get('{http://www.w3.org/XML/1998/namespace}lang') == 'en']
    return (n or [y.text or '' for y in x if _local(y) == 'Name'] or [''])[0]

def _parse(flow):
    if not isinstance(flow, str) or not re.fullmatch('[A-Za-z0-9_]{1,100}', flow):
        raise ValueError('invalid ILO flow')
    f = upstream.dataflows(flow)
    items = [x for x in f['dataflows'] if x['id'] == flow]
    if len(items) != 1:
        raise ValueError('flow not found or ambiguous')
    ref = items[0].get('structure') or {}
    result = upstream.structure(ref.get('agencyID'), ref.get('id'), ref.get('version', 'latest'))
    root = ET.fromstring(result['sdmx_xml'])
    dsds = [x for x in root.iter() if _local(x) == 'DataStructure']
    lists = [x for x in dsds[0].iter() if _local(x) == 'DimensionList'] if len(dsds) == 1 else []
    if len(lists) != 1:
        raise ValueError('unexpected ILO structure')
    cs = {}
    for c in root.iter():
        if _local(c) == 'Codelist':
            key = (c.get('agencyID'), c.get('id'), c.get('version'))
            if key in cs:
                raise ValueError('duplicate codelist')
            cs[key] = [{'code': x.get('id'), 'name': _name(x)} for x in c if _local(x) == 'Code']
    dims = []
    for x in lists[0]:
        if _local(x) != 'Dimension':
            continue
        refs = [y for y in x.iter() if _local(y) == 'Ref' and y.get('class') == 'Codelist']
        if len(refs) > 1:
            raise ValueError('ambiguous code reference')
        c = refs[0] if refs else None
        k = (c.get('agencyID'), c.get('id'), c.get('version')) if c is not None else None
        try:
            position = int(x.get('position', ''))
        except ValueError:
            raise ValueError('invalid dimension position') from None
        dims.append({'id': x.get('id'), 'position': position, 'codelist': k, 'codes': cs.get(k)})
    dims.sort(key=lambda x: x['position'])
    if not dims or [x['position'] for x in dims] != list(range(1, len(dims) + 1)) or len({x['id'] for x in dims}) != len(dims):
        raise ValueError('invalid dimension layout')
    return ({'flow': items[0], 'flow_source': f['source'], 'structure_source': result['source']}, dims)

def dimensions(flow):
    source, dims = _parse(flow)
    return {**source, 'dimensions': [{'id': d['id'], 'position': d['position'], 'codelist': d['codelist'], 'code_count': len(d['codes']) if d['codes'] is not None else None} for d in dims], 'note': '维度依 SDMX key 顺序；流程名称/版本为上游目录原值，不等于数据版次已确认。代码表可选项不保证组合有值。'}

def codes(flow, dimension, keyword='', limit=50, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 100 or type(limit) is not int or (not 1 <= limit <= 500) or (type(offset) is not int) or (offset < 0):
        raise ValueError('invalid code search')
    source, dims = _parse(flow)
    d = next((x for x in dims if x['id'] == dimension), None)
    if not d or d['codes'] is None:
        raise ValueError('dimension or codelist unavailable')
    rows = [x for x in d['codes'] if keyword.casefold() in (str(x['code']) + ' ' + x['name']).casefold()]
    return {**source, 'dimension': dimension, 'matched': len(rows), 'offset': offset, 'next_offset': offset + limit if offset + limit < len(rows) else None, 'codes': rows[offset:offset + limit], 'note': '来源代码表重取时可能变化，代码存在不保证该组合实际有值。'}

def query(flow, selections, start, end):
    if not isinstance(selections, dict):
        raise ValueError('selections must be a dictionary')
    source, dims = _parse(flow)
    byid = {d['id']: d for d in dims}
    if any((x not in byid for x in selections)):
        raise ValueError('unknown dimension')
    parts = []
    for d in dims:
        val = selections.get(d['id'], '')
        if not isinstance(val, str) or (val and (not re.fullmatch('[A-Za-z0-9_-]+(?:\\+[A-Za-z0-9_-]+)*', val))):
            raise ValueError('invalid selected code')
        if d['codes'] is not None and any((x not in {c['code'] for c in d['codes']} for x in val.split('+') if x)):
            raise ValueError('code not in codelist for ' + d['id'])
        parts.append(val)
    key = '.'.join(parts)
    result = upstream.data(flow, key, start, end)
    for row in result['observations']:
        t = row.get('TIME_PERIOD', '')
        if not re.match('^\\d{4}', t) or not start <= int(t[:4]) <= end:
            raise RuntimeError('ILO response outside requested years')
        if any((val and row.get(dim) not in val.split('+') for dim, val in selections.items())):
            raise RuntimeError('ILO response outside selected dimensions')
    result.update({'flow_metadata': source['flow'], 'structure_source': source['structure_source'], 'dimension_selections': selections, 'sdmx_key': key})
    result['note'] += ' 流程名称为上游原值，不推断响应数据版本；估计和预测须核对来源。'
    return result
