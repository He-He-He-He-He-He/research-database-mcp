"""UNICEF SDMX discovery and dimension-based queries using source structures."""
import release_runtime
import re
import unicef_sdmx_general_adapter as upstream

def _structure(agency, flow):
    result = upstream.structure(agency, flow)
    data = result['sdmx']['data']
    flows = [v for v in data['dataflows'] if v.get('agencyID') == agency and v.get('id') == flow]
    structures = data['dataStructures']
    if len(flows) != 1 or len(structures) != 1:
        raise ValueError('expected one matching flow and one structure')
    dimlist = structures[0]['dataStructureComponents']['dimensionList']
    dims = sorted(dimlist.get('dimensions', []), key=lambda x: x['position'])
    if not dims or len({x['position'] for x in dims}) != len(dims):
        raise ValueError('invalid dimension list')
    lists = {}
    for c in data.get('codelists', []):
        for link in c.get('links', []):
            if link.get('urn'):
                lists[link['urn']] = c
    return (result['source'], flows[0], dims, lists)

def dimensions(agency, flow):
    source, item, dims, lists = _structure(agency, flow)
    out = []
    for d in dims:
        enum = d.get('localRepresentation', {}).get('enumeration')
        codes = lists.get(enum)
        out.append({'id': d['id'], 'position': d['position'], 'enumeration': enum, 'codelist': codes.get('name') if codes else None, 'code_count': len(codes.get('codes', [])) if codes else None})
    return {'source': source, 'flow': item['id'], 'version': item['version'], 'dimensions': out, 'note': 'Structure codes are allowed values, not proof that every combination has data. Time uses start/end.'}

def codes(agency, flow, dimension, keyword='', limit=50, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 200 or type(limit) is not int or (not 1 <= limit <= 200) or (type(offset) is not int) or (offset < 0):
        raise ValueError('invalid keyword, limit or offset')
    source, _, dims, lists = _structure(agency, flow)
    matches = [d for d in dims if d['id'] == dimension]
    if len(matches) != 1:
        raise ValueError('unknown dimension')
    enum = matches[0].get('localRepresentation', {}).get('enumeration')
    codelist = lists.get(enum)
    if not codelist:
        raise ValueError('dimension does not have an available code list')
    vals = [c for c in codelist.get('codes', []) if keyword.casefold() in (str(c.get('id', '')) + ' ' + str(c.get('name', ''))).casefold()]
    return {'source': source, 'dimension': dimension, 'codelist': codelist.get('name'), 'matching_count': len(vals), 'offset': offset, 'codes': [{'id': c.get('id'), 'name': c.get('name'), 'description': c.get('description')} for c in vals[offset:offset + limit]], 'note': 'Code-list membership does not guarantee observations exist for a selection.'}

def query(agency, flow, start, end, selections):
    source, item, dims, lists = _structure(agency, flow)
    if not isinstance(selections, dict) or len(selections) < 2:
        raise ValueError('select at least two dimensions')
    by_id = {d['id']: d for d in dims}
    if set(selections) - set(by_id):
        raise ValueError('unknown dimension')
    parts = []
    for d in dims:
        vals = selections.get(d['id'], [])
        if not isinstance(vals, list) or len(vals) > 20 or any((not isinstance(v, str) or not re.fullmatch('[A-Za-z0-9_]{1,100}', v) for v in vals)):
            raise ValueError('selection values must be a list of codes')
        enum = d.get('localRepresentation', {}).get('enumeration')
        codelist = lists.get(enum)
        if vals and (not codelist):
            raise ValueError('cannot validate selected dimension codes')
        if codelist and set(vals) - {c.get('id') for c in codelist.get('codes', [])}:
            raise ValueError('unknown code for ' + d['id'])
        parts.append('+'.join(vals))
    if sum((bool(v) for v in parts)) < 2:
        raise ValueError('select at least two nonempty dimensions')
    result = upstream.data(agency, flow, item['version'], '.'.join(parts), start, end)
    for row in result['observations']:
        for key, vals in selections.items():
            if vals and row.get(key) not in vals:
                raise ValueError('upstream returned a mismatched ' + key)
    result['structure_source'] = source
    result['selection'] = selections
    result['note'] = 'Original values, units, sources and status fields are preserved; observations may be estimates. Code lists do not guarantee data.'
    return result
