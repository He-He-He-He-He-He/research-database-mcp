"""Readable OECD SDMX dimension discovery and named-dimension querying."""
import release_runtime
import re, xml.etree.ElementTree as ET
import oecd_sdmx_general_adapter as upstream

def _local(e):
    return e.tag.rsplit('}', 1)[-1]

def _name(e):
    vals = [x.text or '' for x in e if _local(x) == 'Name']
    en = [x.text or '' for x in e if _local(x) == 'Name' and x.get('{http://www.w3.org/XML/1998/namespace}lang') == 'en']
    return (en or vals or [''])[0]

def _parse(agency, flow, version):
    result = upstream.structure(agency, flow, version)
    root = ET.fromstring(result['sdmx_xml'])
    dsds = [x for x in root.iter() if _local(x) == 'DataStructure']
    if len(dsds) != 1:
        raise ValueError('structure contains multiple or no data structures; inspect original XML')
    lists = [x for x in dsds[0].iter() if _local(x) == 'DimensionList']
    if len(lists) != 1:
        raise ValueError('unexpected dimension structure')
    available = {}
    for c in root.iter():
        if _local(c) != 'Codelist':
            continue
        key = (c.get('agencyID'), c.get('id'), c.get('version'))
        if key in available:
            raise ValueError('duplicate codelist identity')
        available[key] = [{'code': x.get('id'), 'name': _name(x)} for x in c if _local(x) == 'Code']
    dims = []
    for item in lists[0]:
        if _local(item) != 'Dimension':
            continue
        try:
            pos = int(item.get('position', ''))
        except ValueError:
            raise ValueError('missing dimension position') from None
        refs = [x for x in item.iter() if _local(x) == 'Ref' and x.get('class') == 'Codelist']
        if len(refs) > 1:
            raise ValueError('ambiguous codelist reference')
        ref = refs[0] if refs else None
        key = (ref.get('agencyID'), ref.get('id'), ref.get('version')) if ref is not None else None
        dims.append({'id': item.get('id'), 'position': pos, 'codelist': key, 'codes': available.get(key)})
    if not dims or len({x['position'] for x in dims}) != len(dims) or len({x['id'] for x in dims}) != len(dims):
        raise ValueError('invalid dimension list')
    dims.sort(key=lambda x: x['position'])
    if [x['position'] for x in dims] != list(range(1, len(dims) + 1)):
        raise ValueError('non-contiguous SDMX dimension positions')
    return (result['source'], dims)

def dimensions(agency, flow, version):
    source, dims = _parse(agency, flow, version)
    return {'source': source, 'dimensions': [{'id': d['id'], 'position': d['position'], 'codelist': d['codelist'], 'code_count': len(d['codes']) if d['codes'] is not None else None} for d in dims], 'note': '维度按 SDMX key 顺序；代码表是结构所允许代码，不保证各组合均有数据；时间通过独立时间参数选择。'}

def codes(agency, flow, version, dimension, keyword='', limit=50, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 100 or type(limit) is not int or (not 1 <= limit <= 500) or (type(offset) is not int) or (offset < 0):
        raise ValueError('invalid search')
    source, dims = _parse(agency, flow, version)
    d = next((x for x in dims if x['id'] == dimension), None)
    if d is None:
        raise ValueError('unknown dimension')
    if d['codes'] is None:
        raise ValueError('no embedded codelist; consult original structure')
    rows = [x for x in d['codes'] if keyword.casefold() in (str(x['code']) + ' ' + x['name']).casefold()]
    return {'source': source, 'dimension': dimension, 'matched': len(rows), 'offset': offset, 'next_offset': offset + limit if offset + limit < len(rows) else None, 'codes': rows[offset:offset + limit], 'note': '以官方结构代码表本地筛选，跨请求结构可能更新；代码存在不代表选定组合有数据。'}

def query(agency, flow, version, selections, start, end):
    if not isinstance(selections, dict):
        raise ValueError('selections must map dimension IDs to codes')
    source, dims = _parse(agency, flow, version)
    byid = {d['id']: d for d in dims}
    if any((k not in byid for k in selections)):
        raise ValueError('unknown dimension selection')
    parts = []
    for d in dims:
        v = selections.get(d['id'], '')
        if not isinstance(v, str) or (v and (not re.fullmatch('[A-Za-z0-9_-]+(?:\\+[A-Za-z0-9_-]+)*', v))):
            raise ValueError('invalid code selection')
        values = v.split('+') if v else []
        if d['codes'] is not None and any((x not in {c['code'] for c in d['codes']} for x in values)):
            raise ValueError('code not in dimension codelist: ' + d['id'])
        parts.append(v)
    key = '.'.join(parts)
    result = upstream.data(agency, flow, version, key, start, end)
    result['dimension_selections'] = selections
    result['sdmx_key'] = key
    result['structure_source'] = source
    result['note'] += ' 代码表允许的值并不保证有观测；结构与数据可能更新。'
    return result
