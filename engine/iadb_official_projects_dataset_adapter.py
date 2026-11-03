"""Inter-American Development Bank official project list (English resource)."""
import release_runtime
import json, re, requests
URL = 'https://data.iadb.org/api/3/action/datastore_search'
RESOURCE = '814b7b54-477a-4c25-b3bf-6be05412069d'
CATALOG = 'https://data.iadb.org/dataset/idb-projects-dataset'

def query(country, limit=20, offset=0):
    if not isinstance(country, str) or not re.fullmatch('[A-Za-z]{2}', country):
        raise ValueError('country must be IDB two-letter code')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or (not 0 <= offset <= 100000):
        raise ValueError('invalid pagination')
    country = country.upper()
    p = {'resource_id': RESOURCE, 'filters': json.dumps({'cntry_cd': country}), 'limit': limit, 'offset': offset, 'sort': '_id asc', 'include_total': 'true'}
    r = requests.get(URL, params=p, timeout=40)
    r.raise_for_status()
    j = r.json()
    v = j.get('result', {})
    if j.get('success') is not True or v.get('resource_id') != RESOURCE or (not isinstance(v.get('records'), list)) or (not isinstance(v.get('total'), int)):
        raise ValueError('unexpected IDB response')
    if any((x.get('cntry_cd') != country for x in v['records'])):
        raise ValueError('server filter mismatch')
    return {'source': URL, 'catalog': CATALOG, 'request': p, 'total': v['total'], 'records': v['records'], 'note': 'IDB project and operation records include preparation and approved projects; status is per row. Original approved, total cost and counterpart amounts are distinct and not actual disbursement; preserve source numeric strings and blank values. IDB country codes may differ from ISO (Honduras is HO, not HN). Country-level selection excludes regional or multicountry entries not individually tagged. Generic IDB datastore API also supports this resource.'}
