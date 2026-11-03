"""UN-Habitat public South Africa historical urban land consumption sample."""
import release_runtime
import requests
BASE = 'https://services6.arcgis.com/uWtJiVzcBsV6C7NV/arcgis/rest/services/11_3_1_Land_Consumption_Rates_in_South_Africa/FeatureServer/0'
CATALOG = 'https://data.unhabitat.org/api/search/v1/collections/dataset/items/cc8c17fb67aa496e9feba634cec92446'

def records(limit=10, offset=0):
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('limit must be 1–100')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 0 <= offset <= 10000):
        raise ValueError('invalid offset')
    r = requests.get(BASE + '/query', params={'where': '1=1', 'outFields': '*', 'returnGeometry': 'false', 'resultOffset': offset, 'resultRecordCount': limit, 'orderByFields': 'ObjectId', 'f': 'json'}, timeout=35)
    r.raise_for_status()
    d = r.json()
    if not isinstance(d.get('features'), list):
        raise ValueError('unexpected ArcGIS response')
    return {'source': 'UN-Habitat Urban Indicators Database; estimate source recorded per row', 'catalog': CATALOG, 'license': 'not specified in source catalog', 'offset': offset, 'returned': len(d['features']), 'has_more': d.get('exceededTransferLimit', False), 'fields': d.get('fields', []), 'items': [x['attributes'] for x in d['features']], 'note': 'Historical selected South African cities; do not interpret as current nationwide total. Ratios and rates retain original scale.'}
