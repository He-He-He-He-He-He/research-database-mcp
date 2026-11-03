"""Portugal LNEG mineral-deposit and potential-area map attributes."""
import release_runtime
import requests
BASE = 'https://sig.lneg.pt/server/rest/services/'
SERVICES = {'deposits': 'CartaDepositosMinerais200k', 'potential': 'AreasPotenciaisRecursosMinerais'}
NOTES = ['Portuguese national energy and geology laboratory LNEG. Mineral deposit map is at 1:200,000 scale; map detail is not site-level verification.', 'Potential mineral areas indicate geological prospectivity, not confirmed commercial reserves, current permits, operating mines or a resource estimate.', 'Raw attributes, blank strings and placeholders are retained. Production and tonnage field units and dates require original documentation.', 'Coverage and map status may change. Current service and access timestamps do not prove historical availability; consult LNEG for licence and reuse terms.']

def _get(url, params=None):
    r = requests.get(url, params=params, timeout=40)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, dict) or 'error' in j:
        raise ValueError('LNEG service error: ' + str(j.get('error', 'invalid response')))
    return j

def _url(kind, layer):
    if kind not in SERVICES or type(layer) is not int or (kind == 'deposits' and layer != 0) or (kind == 'potential' and (not 0 <= layer <= 8)):
        raise ValueError('Invalid service or layer')
    return BASE + SERVICES[kind] + '/MapServer/' + str(layer)

def metadata(kind, layer):
    url = _url(kind, layer)
    j = _get(url, {'f': 'json'})
    if not isinstance(j.get('fields'), list):
        raise ValueError('Unexpected layer metadata')
    service = _get(BASE + SERVICES[kind] + '/MapServer', {'f': 'json'})
    return {'source': url, 'notes': NOTES, 'service_metadata': service, 'layer_metadata': j}

def records(kind, layer, limit=10, offset=0):
    url = _url(kind, layer)
    if type(limit) is not int or not 1 <= limit <= 100 or type(offset) is not int or (not 0 <= offset <= 100000):
        raise ValueError('Invalid pagination')
    meta = metadata(kind, layer)
    oid = meta['layer_metadata'].get('objectIdField') or meta['layer_metadata'].get('objectIdFieldName') or next((f.get('name') for f in meta['layer_metadata']['fields'] if f.get('type') == 'esriFieldTypeOID'), None)
    if not isinstance(oid, str) or not oid.replace('_', '').isalnum():
        raise ValueError('Missing object ID')
    j = _get(url + '/query', {'f': 'json', 'where': '1=1', 'outFields': '*', 'returnGeometry': 'false', 'orderByFields': oid + ' ASC', 'resultOffset': offset, 'resultRecordCount': limit})
    if not isinstance(j.get('features'), list):
        raise ValueError('Unexpected feature response')
    return {'source': url + '/query', 'notes': NOTES, 'service_metadata': meta['service_metadata'], 'layer_metadata': meta['layer_metadata'], 'offset': offset, 'response': j}
