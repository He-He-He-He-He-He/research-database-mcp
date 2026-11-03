"""US DOE-hosted NGA World Port Index layer; mirror, not NGA live service."""
import release_runtime
import requests
BASE = 'https://arcgis.netl.doe.gov/server/rest/services/Hosted/CCS_EJ_SJ_Data/FeatureServer/17'
PRIMARY = 'https://msi.nga.mil/Publications/WPI'

def _get(path='', params=None):
    r = requests.get(BASE + path, params=params, timeout=35)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, dict) or 'error' in j:
        raise ValueError('unexpected ArcGIS response')
    return j

def search(country, limit=20, offset=0):
    if not isinstance(country, str) or not country.strip() or len(country) > 100 or any((c in country for c in ('\n', '\r', '\x00'))):
        raise ValueError('invalid country')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or offset < 0:
        raise ValueError('invalid pagination')
    where = "wpi_cc = '" + country.replace("'", "''") + "'"
    meta = _get('', {'f': 'json'})
    count = _get('/query', {'where': where, 'returnCountOnly': 'true', 'f': 'json'})
    p = {'where': where, 'outFields': '*', 'returnGeometry': 'true', 'outSR': '4326', 'resultRecordCount': limit, 'resultOffset': offset, 'orderByFields': 'wpinumber ASC', 'f': 'json'}
    result = _get('/query', p)
    if not isinstance(count.get('count'), int) or not isinstance(result.get('features'), list):
        raise ValueError('unexpected query response')
    if any((not isinstance(x, dict) or x.get('attributes', {}).get('wpi_cc', '').casefold() != country.casefold() for x in result['features'])):
        raise ValueError('out-of-filter result')
    return {'source': BASE, 'primary_source': PRIMARY, 'request': p, 'mirror_last_edit_ms': meta.get('editingInfo', {}).get('lastEditDate'), 'total': count['count'], 'offset': offset, 'rows': result['features'], 'note': 'US Department of Energy mirror of NGA World Port Index, not the live authoritative NGA publication; mirror can be stale. Major ports/terminals only, not every port or traffic statistics. Field units and coded values follow layer metadata; location/capacity may change. Not for navigation or operational decisions; verify current official charts and port authorities.'}
