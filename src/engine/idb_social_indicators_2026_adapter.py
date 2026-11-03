"""IDB Social Indicators of Latin America, using the bank's CKAN DataStore."""
import release_runtime
import re
import iadb_opendata_adapter as idb
DATA = 'ba412771-9c90-4613-a96a-e18c005c0ab6'
DICT = 'f786c09e-7602-41a6-be52-d8a09f12f56e'
PAGE = 'https://data.iadb.org/dataset/social-indicators-of-latin-america-and-the-caribbean'
CITE = 'Inter-American Development Bank (2026). Social Indicators of Latin America and the Caribbean. IDB Open Data. https://doi.org/10.60966/qtp2zxqd'

def metadata(indicator):
    if not isinstance(indicator, str) or not re.fullmatch('[A-Za-z0-9_]{1,60}', indicator):
        raise ValueError('Invalid IDB indicator code')
    result = idb.records(DICT, {'indicator': indicator}, 0, 100)['result']
    if any((x.get('indicator') != indicator for x in result['records'])):
        raise RuntimeError('IDB metadata filter was not applied')
    return {'source': 'Inter-American Development Bank', 'dataset_page': PAGE, 'citation': CITE, 'license': 'CC BY 4.0', 'metadata': result}

def data(country, indicator, year, offset=0, limit=20):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('Country must be an ISO3 code')
    if not isinstance(year, int) or isinstance(year, bool) or (not 1900 <= year <= 2100):
        raise ValueError('Invalid year')
    meta = metadata(indicator)
    if not meta['metadata']['records']:
        raise ValueError('Indicator absent from IDB dictionary')
    filters = {'isoalpha3': country, 'indicator': indicator, 'year': year}
    result = idb.records(DATA, filters, offset, limit)['result']
    if any((any((row.get(k) != v for k, v in filters.items())) for row in result['records'])):
        raise RuntimeError('IDB data filter was not applied')
    return {'source': 'Inter-American Development Bank', 'dataset_page': PAGE, 'citation': CITE, 'license': 'CC BY 4.0', 'indicator_definitions': meta['metadata']['records'], 'data': result, 'note': 'IDB harmonized household survey/census indicators, not national official statistics. Values, estimated standard errors, samples and quality flags are unchanged; source, survey coverage, categories and scales must be checked. Total and subgroup rows overlap; do not sum them. An indicator labelled percentage may be stored as a 0–1 fraction; do not assume without checking metadata.'}
