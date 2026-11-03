"""Global Fund data service v4.2 OData catalogue, schema and bounded records."""
import release_runtime
import json, re, requests, xml.etree.ElementTree as ET
BASE = 'https://fetch.theglobalfund.org/v4.2/odata/'
PAGE = 'https://data-service.theglobalfund.org/api'

def _get(path, params=None, xml=False):
    with requests.get(BASE + path, params=params, headers={'Accept': 'application/xml' if xml else 'application/json'}, timeout=(15, 40), stream=True) as r:
        r.raise_for_status()
        chunks = []
        size = 0
        for b in r.iter_content(65536):
            size += len(b)
            if size > 5000000:
                raise RuntimeError('Global Fund response exceeds 5 MB')
            chunks.append(b)
    raw = b''.join(chunks)
    if xml:
        return ET.fromstring(raw)
    x = json.loads(raw)
    if not isinstance(x, dict) or not isinstance(x.get('value'), list):
        raise RuntimeError('Unexpected Global Fund OData response')
    return x

def catalogue():
    x = _get('')
    return {'source': 'The Global Fund', 'documentation': PAGE, 'api_version': '4.2', 'items': x['value'], 'note': 'Dataset information includes dataset-specific licence and update information.'}

def structure(entity):
    if not isinstance(entity, str) or not re.fullmatch('[A-Za-z][A-Za-z0-9]{0,79}', entity):
        raise ValueError('Invalid entity name')
    root = _get('$metadata', xml=True)
    edm = '{http://docs.oasis-open.org/odata/ns/edm}'
    matches = [e for e in root.iter(edm + 'EntitySet') if e.get('Name') == entity]
    if len(matches) != 1:
        raise ValueError('Unknown or ambiguous Global Fund entity')
    entity_type = matches[0].get('EntityType')
    local = entity_type.rsplit('.', 1)[-1]
    types = [e for e in root.iter(edm + 'EntityType') if e.get('Name') == local]
    if len(types) != 1:
        raise RuntimeError('Ambiguous entity type')
    props = [dict(p.attrib) for p in types[0].findall(edm + 'Property')]
    return {'source': 'The Global Fund', 'documentation': PAGE, 'entity': entity, 'entity_type': entity_type, 'fields': props, 'note': 'Field types are from official OData metadata; see DatasetInformation and terms for definitions and licence.'}

def data(entity, field='', value='', value_type='string', offset=0, limit=20):
    if not isinstance(entity, str) or not re.fullmatch('[A-Za-z][A-Za-z0-9]{0,79}', entity):
        raise ValueError('Invalid entity name')
    if not isinstance(field, str) or not isinstance(value, str) or bool(field) != bool(value) or (len(value) > 120):
        raise ValueError('Provide both field and value or neither')
    if value_type not in ('string', 'guid'):
        raise ValueError('Type must be string or guid')
    if not isinstance(offset, int) or isinstance(offset, bool) or (not 0 <= offset <= 100000) or (not isinstance(limit, int)) or isinstance(limit, bool) or (not 1 <= limit <= 100):
        raise ValueError('Invalid pagination')
    schema = structure(entity)
    fields = {p['Name']: p['Type'] for p in schema['fields']}
    params = {'$top': limit, '$skip': offset}
    if field:
        if field not in fields:
            raise ValueError('Unknown field')
        if value_type == 'guid':
            if fields[field] != 'Edm.Guid' or not re.fullmatch('[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', value):
                raise ValueError('Expected GUID field and GUID value')
            literal = value
        else:
            if fields[field] != 'Edm.String':
                raise ValueError('Selected field is not string')
            literal = "'" + value.replace("'", "''") + "'"
        params['$filter'] = field + ' eq ' + literal
    x = _get(entity, params)
    if len(x['value']) > limit:
        raise RuntimeError('Global Fund exceeded requested page size')
    if field and any((str(row.get(field, '')).lower() != value.lower() for row in x['value'])):
        raise RuntimeError('Global Fund returned records outside requested filter')
    return {'source': 'The Global Fund', 'documentation': PAGE, 'api_version': '4.2', 'entity': entity, 'filter': {'field': field, 'value': value, 'type': value_type}, 'offset': offset, 'limit': limit, 'next_link': x.get('@odata.nextLink'), 'page_full': len(x['value']) == limit, 'items': x['value'], 'note': 'Financial, commitments, signed, and disbursement figures have distinct meanings and may overlap; do not add as separate financing. Respect dataset licence and preserve original fields and currency. The server may omit nextLink even when later records exist; a full page is not proof either way. Offset paging has no stable snapshot guarantee.'}
