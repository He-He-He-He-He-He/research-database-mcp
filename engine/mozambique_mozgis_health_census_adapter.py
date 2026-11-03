"""Mozambique government GIS health facilities and census attributes."""
import release_runtime
import requests
BASE = 'https://www.mozgis.gov.mz/server/rest/services/MISAU/EDUSUnidadesSanitarias/FeatureServer'
LAYERS = {1: 'Hospitais', 2: 'Centros de Saúde', 3: 'Postos de Saúde', 5: 'Província (Censo 2017)', 6: 'Distrito (Censo 2017)'}
NOTES = ['Source is the Mozambique government GIS health service; retain the returned layer metadata, fields, descriptions and source licence when interpreting or reusing data.', 'Layers 5 and 6 refer to the 2017 census; T denotes total, H men and M women according to the layer description. Confirm the rest of each field definition before analysis.', 'Health facility coverage, operational status and update dates are not independently verified. Records must not be assumed current or exhaustive.', 'Do not add individual ages to age groups, or sum overlapping fields. Current service availability does not prove this file was available at a historical cutoff.']

def _get(path, params):
    r = requests.get(BASE + path, params=params, timeout=45)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, dict) or 'error' in j:
        raise ValueError('Mozambique GIS service error: ' + str(j.get('error', 'invalid response')))
    return j

def metadata(layer):
    if type(layer) is not int or layer not in LAYERS:
        raise ValueError('Unknown layer')
    j = _get('/' + str(layer), {'f': 'json'})
    if not isinstance(j.get('fields'), list):
        raise ValueError('Unexpected layer metadata')
    return {'source': BASE + '/' + str(layer), 'notes': NOTES, 'metadata': j}

def records(layer, limit=10, offset=0):
    if type(layer) is not int or layer not in LAYERS or type(limit) is not int or (not 1 <= limit <= 100) or (type(offset) is not int) or (not 0 <= offset <= 100000):
        raise ValueError('Invalid layer, limit, or offset')
    m = metadata(layer)['metadata']
    oid = m.get('objectIdField')
    if not isinstance(oid, str) or not oid.replace('_', '').isalnum():
        raise ValueError('Missing object ID field')
    j = _get('/' + str(layer) + '/query', {'f': 'json', 'where': '1=1', 'outFields': '*', 'returnGeometry': 'false', 'resultOffset': offset, 'resultRecordCount': limit, 'orderByFields': oid + ' ASC'})
    if not isinstance(j.get('features'), list):
        raise ValueError('Unexpected query response')
    return {'source': BASE + '/' + str(layer) + '/query', 'layer_metadata': m, 'offset': offset, 'limit': limit, 'notes': NOTES, 'response': j}
