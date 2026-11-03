"""Albania INSTAT public ArcGIS GeoData Hub items and tabular layer data."""
import release_runtime
import argparse, json, re
from urllib.parse import urlparse
import requests
PORTAL = 'https://instat.maps.arcgis.com/sharing/rest'

def get(url, params):
    s = requests.Session()
    s.trust_env = False
    with s.get(url, params=params, timeout=35, stream=True) as r:
        r.raise_for_status()
        buf = bytearray()
        for chunk in r.iter_content(65536):
            buf.extend(chunk)
            if len(buf) > 8000000:
                raise ValueError('Response exceeds 8 MB')
        data = json.loads(buf)
        if isinstance(data, dict) and 'error' in data:
            raise ValueError(str(data['error']))
        return (data, r.url)

def catalog(keyword='', limit=20, start=1):
    if not 1 <= limit <= 100 or not 1 <= start <= 10000:
        raise ValueError('limit 1–100 and start 1–10000')
    if keyword and (not re.fullmatch('[\\w\\s.-]{1,100}', keyword)):
        raise ValueError('Invalid keyword')
    q = 'owner:INSTAT' + (' AND ' + keyword if keyword else '')
    data, url = get(PORTAL + '/search', {'f': 'json', 'q': q, 'num': limit, 'start': start})
    return {'source': url, 'total': data.get('total'), 'nextStart': data.get('nextStart'), 'items': data.get('results', []), 'note': 'Search returns various item types; inspect item metadata and license.'}

def item(itemid):
    if not re.fullmatch('[0-9a-fA-F]{32}', itemid):
        raise ValueError('Invalid item id')
    data, url = get(PORTAL + '/content/items/' + itemid, {'f': 'json'})
    if str(data.get('owner', '')).lower() != 'instat':
        raise ValueError('Item is not owned by INSTAT')
    return {'source': url, 'item': data}

def service(itemid):
    obj = item(itemid)['item']
    url = obj.get('url', '')
    p = urlparse(url)
    if obj.get('type') != 'Feature Service' or p.scheme != 'https' or p.hostname != 'services7.arcgis.com' or (not p.path.startswith('/E9FE1JuiACmTPbPv/arcgis/rest/services/')) or (not p.path.endswith('/FeatureServer')):
        raise ValueError('Item is not an INSTAT Feature Service')
    return url

def layers(itemid):
    d, u = get(service(itemid), {'f': 'json'})
    return {'source': u, 'layers': d.get('layers'), 'tables': d.get('tables')}

def metadata(itemid, layer):
    if not 0 <= layer <= 1000:
        raise ValueError('Invalid layer')
    d, u = get(service(itemid) + '/' + str(layer), {'f': 'json'})
    return {'source': u, 'name': d.get('name'), 'description': d.get('description'), 'fields': d.get('fields'), 'maxRecordCount': d.get('maxRecordCount')}

def data(itemid, layer, limit, offset):
    if not 1 <= limit <= 100 or not 0 <= offset <= 100000:
        raise ValueError('limit 1–100 and offset 0–100000')
    meta = metadata(itemid, layer)
    fields = meta['fields']
    oid = next((x['name'] for x in fields if x.get('type') == 'esriFieldTypeOID'), None)
    p = {'f': 'json', 'where': '1=1', 'outFields': '*', 'returnGeometry': 'false', 'resultRecordCount': limit, 'resultOffset': offset}
    if oid:
        p['orderByFields'] = oid + ' ASC'
    d, u = get(service(itemid) + '/' + str(layer) + '/query', p)
    return {'source': u, 'metadata_source': meta['source'], 'fieldAliases': d.get('fieldAliases'), 'rows': [x['attributes'] for x in d.get('features', [])], 'exceededTransferLimit': d.get('exceededTransferLimit', False), 'note': 'Use item description and license for meaning and permissions. Values are not unit-converted.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='command', required=True)
    c = s.add_parser('catalog')
    c.add_argument('--keyword', default='')
    c.add_argument('--limit', type=int, default=20)
    c.add_argument('--start', type=int, default=1)
    for name in ['item', 'layers', 'metadata', 'data']:
        x = s.add_parser(name)
        x.add_argument('itemid')
        if name in ['metadata', 'data']:
            x.add_argument('--layer', type=int, default=0)
        if name == 'data':
            x.add_argument('--limit', type=int, default=20)
            x.add_argument('--offset', type=int, default=0)
    a = p.parse_args()
    res = catalog(a.keyword, a.limit, a.start) if a.command == 'catalog' else item(a.itemid) if a.command == 'item' else layers(a.itemid) if a.command == 'layers' else metadata(a.itemid, a.layer) if a.command == 'metadata' else data(a.itemid, a.layer, a.limit, a.offset)
    print(json.dumps(res, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
