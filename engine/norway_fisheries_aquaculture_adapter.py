"""Norwegian Directorate of Fisheries aquaculture location register."""
import release_runtime
import re
import requests
URL = 'https://gis.fiskeridir.no/server/rest/services/Yggdrasil/Akvakulturregisteret/FeatureServer/0'
NOTES = ['Source is the Directorate of Fisheries aquaculture register; records describe approved aquaculture locations, not actual fish production or current biomass.', 'Capacity refers to approved/current authorised capacity as labelled by the source, and the unit is provided separately in kapasitet_unittype; it is not production volume.', 'Status and permits are current source records at retrieval and can change. A clearance date is not evidence of historic capacity or an earlier data snapshot.', 'Original fields and date epoch values are retained; confirm unit, status, licensing and original documentation before use. Data use is subject to Norway Open Government Data Licence (NLOD).']

def _get(path='', params=None):
    r = requests.get(URL + path, params=params, timeout=45)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, dict) or 'error' in j:
        raise ValueError('Fisheries service error: ' + str(j.get('error', 'invalid response')))
    return j

def metadata():
    j = _get(params={'f': 'json'})
    if not isinstance(j.get('fields'), list):
        raise ValueError('Unexpected metadata')
    return {'source': URL, 'notes': NOTES, 'metadata': j}

def records(county=None, limit=10, offset=0):
    if county is not None and (not isinstance(county, str) or not re.fullmatch('[\\w -]{1,80}', county)):
        raise ValueError('Invalid county')
    if type(limit) is not int or not 1 <= limit <= 100 or type(offset) is not int or (not 0 <= offset <= 100000):
        raise ValueError('Invalid pagination')
    where = "fylke = '" + county + "'" if county else '1=1'
    j = _get('/query', {'f': 'json', 'where': where, 'outFields': '*', 'returnGeometry': 'false', 'resultOffset': offset, 'resultRecordCount': limit, 'orderByFields': 'objectid ASC'})
    if not isinstance(j.get('features'), list):
        raise ValueError('Unexpected record response')
    return {'source': URL + '/query', 'county': county, 'notes': NOTES, 'response': j}
