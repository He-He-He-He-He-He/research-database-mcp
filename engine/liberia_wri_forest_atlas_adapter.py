"""WRI Liberia Forest Atlas DCAT catalogue and bounded feature attributes."""
import release_runtime
import requests
CAT = 'https://lbr.forest-atlas.org/api/feed/dcat-us/1.1.json'
BASE = 'https://services2.arcgis.com/g8WusZB13b9OegfU/arcgis/rest/services/'
LAYERS = {'roads': 'Roads_Liberia', 'conservation': 'Conservation_Landscapes', 'counties': 'Counties', 'community': 'Community_Forests_Liberia'}
NOTES = ['WRI / Global Forest Watch Liberia Forest Atlas; source institution, reference date, completeness and licence must be checked separately for each layer.', 'Feature attributes are unmodified, including blanks, zeros and numeric date fields. A recorded Active status is not proof of current legal status.', 'Area fields can use different computations or projections and must not be treated as equivalent without documentation. No geometry is returned.', 'Current availability or catalogue modification dates do not prove a historical version was available at a research cutoff.']

def _get(url, params=None):
    with requests.get(url, params=params, timeout=40, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for chunk in r.iter_content(65536):
            raw.extend(chunk)
            if len(raw) > 10000000:
                raise ValueError('response exceeds size limit')
    import json
    j = json.loads(raw)
    if not isinstance(j, dict) or 'error' in j:
        raise ValueError('Unexpected Atlas response')
    return j

def catalog():
    j = _get(CAT)
    if not isinstance(j.get('dataset'), list):
        raise ValueError('Unexpected catalogue')
    return {'source': CAT, 'notes': NOTES, 'catalog': j}

def metadata(layer):
    if layer not in LAYERS:
        raise ValueError('Unknown layer')
    url = BASE + LAYERS[layer] + '/FeatureServer/0'
    j = _get(url, {'f': 'json'})
    if not isinstance(j.get('fields'), list):
        raise ValueError('Unexpected layer metadata')
    return {'source': url, 'notes': NOTES, 'metadata': j}

def records(layer, limit=10, offset=0):
    if layer not in LAYERS or type(limit) is not int or (not 1 <= limit <= 100) or (type(offset) is not int) or (not 0 <= offset <= 100000):
        raise ValueError('Invalid request')
    m = metadata(layer)['metadata']
    oid = m.get('objectIdField')
    if not isinstance(oid, str) or not oid.replace('_', '').isalnum():
        raise ValueError('Missing object ID')
    url = BASE + LAYERS[layer] + '/FeatureServer/0/query'
    j = _get(url, {'f': 'json', 'where': '1=1', 'outFields': '*', 'returnGeometry': 'false', 'resultOffset': offset, 'resultRecordCount': limit, 'orderByFields': oid + ' ASC'})
    if not isinstance(j.get('features'), list):
        raise ValueError('Unexpected features')
    return {'source': url, 'notes': NOTES, 'layer_metadata': m, 'offset': offset, 'limit': limit, 'response': j}
