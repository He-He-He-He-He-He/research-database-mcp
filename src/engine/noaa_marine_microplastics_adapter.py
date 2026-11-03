"""NOAA NCEI global marine microplastics observation layer (ArcGIS)."""
import release_runtime
import json, math, subprocess
from urllib.parse import urlencode
BASE = 'https://services2.arcgis.com/C8EMgrsFcRFL6LrL/arcgis/rest/services/Marine_Microplastics_WGS84/FeatureServer/0'

def query(west, south, east, north, limit=20, offset=0):
    bounds = (west, south, east, north)
    if any((isinstance(x, bool) or not isinstance(x, (int, float)) or (not math.isfinite(x)) for x in bounds)):
        raise ValueError('coordinates must be finite numbers')
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError('invalid bounding box; split antimeridian-crossing boxes')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 200 or (not 0 <= offset <= 100000):
        raise ValueError('invalid limit or offset')
    params = {'where': '1=1', 'geometry': ','.join(map(str, bounds)), 'geometryType': 'esriGeometryEnvelope', 'inSR': '4326', 'spatialRel': 'esriSpatialRelIntersects', 'outFields': '*', 'returnGeometry': 'false', 'orderByFields': 'OBJECTID ASC', 'resultOffset': offset, 'resultRecordCount': limit, 'f': 'json'}
    url = BASE + '/query?' + urlencode(params)
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '40', '--max-filesize', '5000000', url], capture_output=True, timeout=45)
    if r.returncode:
        raise RuntimeError('NOAA query failed: ' + r.stderr.decode('utf-8', 'replace')[:300])
    if len(r.stdout) > 5000000:
        raise ValueError('NOAA response exceeds 5 MB')
    j = json.loads(r.stdout)
    if 'error' in j:
        raise RuntimeError('NOAA ArcGIS error: ' + str(j['error']))
    if not isinstance(j.get('features'), list):
        raise ValueError('unexpected NOAA response')
    return {'source': url, 'metadata': BASE + '?f=pjson', 'offset': offset, 'returned': len(j['features']), 'exceededTransferLimit': j.get('exceededTransferLimit'), 'observations': [f['attributes'] for f in j['features']], 'note': 'Individual observations, not nationally representative averages. Preserve Unit, sampling medium/method, depth, mesh and dates; Date_m_d_yyyy is an ArcGIS epoch-millisecond timestamp. Sampling methods and units differ: do not aggregate across incompatible records. Coverage depends on contributed studies; area names can be null.'}
