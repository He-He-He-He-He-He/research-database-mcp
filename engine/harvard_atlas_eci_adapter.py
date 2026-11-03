"""Harvard Growth Lab Atlas economic complexity country-year queries."""
import release_runtime
import requests
URL = 'https://atlas.hks.harvard.edu/api/graphql'

def _graphql(query, variables=None):
    with requests.post(URL, json={'query': query, 'variables': variables or {}}, timeout=30, stream=True) as r:
        r.raise_for_status()
        payload = r.raw.read(1000001, decode_content=True)
    if len(payload) > 1000000:
        raise ValueError('response exceeds size limit')
    import json
    result = json.loads(payload)
    if result.get('errors'):
        raise RuntimeError('Atlas GraphQL returned errors: ' + str(result['errors']))
    return result['data']

def countries():
    q = '{ locationCountry { countryId iso3Code nameEn } }'
    entries = _graphql(q)['locationCountry']
    for entry in entries:
        raw = entry.get('countryId', '')
        entry['query_id'] = int(raw.removeprefix('country-')) if raw.startswith('country-') and raw.removeprefix('country-').isdigit() else None
    return entries

def query(country_id, year_from, year_to):
    if type(country_id) is not int or not 1 <= country_id <= 9999:
        raise ValueError('country_id must be a positive Atlas country ID')
    if not 1962 <= year_from <= year_to <= 2100 or year_to - year_from > 50:
        raise ValueError('invalid year range; maximum span is 51 years')
    q = 'query($id:Int!,$start:Int!,$end:Int!){countryYear(countryId:$id,yearMin:$start,yearMax:$end){year eci}}'
    records = _graphql(q, {'id': country_id, 'start': year_from, 'end': year_to})['countryYear']
    return {'source': 'Harvard Growth Lab Atlas of Economic Complexity', 'source_url': URL, 'country_id': country_id, 'indicator': 'Economic Complexity Index (ECI)', 'unit': 'dimensionless index', 'records': records, 'note': 'Research estimate based on export structure, not government statistics. Atlas API documentation limits requests and recommends independent analysis rather than powering other applications; redistribution rights are not verified.'}
