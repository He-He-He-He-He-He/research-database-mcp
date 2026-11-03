"""World Bank Finances One official IPF contract awards API, FY2020 onward."""
import release_runtime
import requests
API = 'https://datacatalogapi.worldbank.org/dexapps/fone/api/apiservice'
DOC = 'https://financesone.worldbank.org/api-explorer?id=DS00005'
DATASET = 'https://financesone.worldbank.org/d/DS00005'

def contracts(offset=0, limit=20):
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError('offset must be a nonnegative integer')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 1000):
        raise ValueError('limit must be an integer from 1 to 1000')
    response = requests.get(API, params={'datasetId': 'DS00005', 'resourceId': 'RS00005', 'type': 'json', 'top': limit, 'skip': offset}, timeout=60)
    response.raise_for_status()
    value = response.json()
    if not isinstance(value, dict) or not isinstance(value.get('data'), list) or (not isinstance(value.get('count'), int)):
        raise ValueError('unexpected World Bank response shape')
    return {'source': API, 'documentation': DOC, 'dataset': DATASET, 'license': 'https://creativecommons.org/licenses/by/4.0/', 'offset': offset, 'limit': limit, 'total': value['count'], 'rows': value['data'], 'notes': ['Contract awards in World Bank Investment Project Financing since FY2020; this is not all procurement in a country.', 'supplier_contract_amount_usd is a committed amount in US dollars, converted at the US Treasury rate when the Bank gave no objection; it is not a disbursement.', 'Multiple supplier records can share the same contract number and repeated amount; do not sum rows as independent awards without inspecting the contract and supplier definitions.', 'Fiscal years run July 1 to June 30. A record as_of_date is a snapshot date; the dataset and paging may change.', 'Pages use the official top and skip parameters. Stable ordering across separate requests has not been established.']}
