"""Swiss federal geoportal point height and layer metadata."""
import release_runtime
import math
import requests
BASE = 'https://api3.geo.admin.ch/rest/services/'
NOTES = ['Federal geoportal: output comes from a terrain model, not a direct ground survey. Verify model version, resolution, vertical reference, and uncertainty for the intended use.', 'Input must be Swiss projected coordinates: EPSG:2056 LV95 or EPSG:21781 LV03, not latitude/longitude.', 'Outside Switzerland the service uses a combined 10-metre elevation model in the documented coverage; values beyond coverage may be absent.', 'Current values may change with updates. An observation is not a historical snapshot; users must follow geo.admin.ch terms of use and source-specific licences.']

def _get(path, params):
    r = requests.get(BASE + path, params=params, timeout=40)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, dict) or j.get('error'):
        raise ValueError('Geoportal response error')
    return j

def height(easting, northing, sr=2056):
    if isinstance(easting, bool) or isinstance(northing, bool) or (not isinstance(easting, (int, float))) or (not isinstance(northing, (int, float))) or (not math.isfinite(easting)) or (not math.isfinite(northing)) or (sr not in (2056, 21781)):
        raise ValueError('Invalid Swiss projected coordinates')
    j = _get('height', {'easting': easting, 'northing': northing, 'sr': sr})
    if 'height' not in j:
        raise ValueError('Unexpected height response')
    return {'source': BASE + 'height', 'coordinate_reference': 'EPSG:' + str(sr), 'easting': easting, 'northing': northing, 'notes': NOTES, 'response': j}

def layers(query, lang='en', limit=20):
    if not isinstance(query, str) or not query.strip() or len(query) > 100 or (lang not in ('en', 'de', 'fr', 'it', 'rm')) or (type(limit) is not int) or (not 1 <= limit <= 100):
        raise ValueError('Invalid layer search')
    j = _get('ech/MapServer', {'searchText': query, 'lang': lang})
    if not isinstance(j.get('layers'), list):
        raise ValueError('Unexpected layer metadata')
    all_layers = j['layers']
    j['layers'] = all_layers[:limit]
    return {'source': BASE + 'ech/MapServer', 'query': query, 'total_returned_by_source': len(all_layers), 'shown': len(j['layers']), 'notes': NOTES, 'response': j}
