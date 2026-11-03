"""Peru MEF open data catalogue and bounded datastore query."""
import release_runtime
import re
import uuid
import requests
PORTAL = 'https://datosabiertos.mef.gob.pe/Rest/'
DATA = 'https://api.datosabiertos.mef.gob.pe/DatosAbiertos/v1/datastore_search'
NOTES = ['Official Peru Ministry of Economy and Finance open data: check each dataset description and dictionary for units, scope, licence, reference periods and update frequency.', 'Budget allocation, committed expenditure, accrued expenditure and payments are distinct fiscal stages; do not treat them as interchangeable.', 'Raw API values and nulls are preserved. Dataset and resource descriptions can disagree about coverage; inspect both.', 'Current resources may be revised; metadata creation or modification dates do not prove a historical snapshot existed at a chosen cutoff.']

def _post(path, body):
    r = requests.post(PORTAL + path, json=body, timeout=40)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, dict):
        raise ValueError('Unexpected MEF response')
    return j

def search(keyword, page=1):
    if not isinstance(keyword, str) or len(keyword) > 150 or type(page) is not int or (not 1 <= page <= 1000):
        raise ValueError('Invalid catalogue query')
    j = _post('PortalWebDatasets/v1.0/getDatasets', {'search': keyword, 'sort': '', 'tags': [], 'formats': [], 'categories': [], 'page': page})
    if not isinstance(j.get('datasets'), list):
        raise ValueError('Unexpected MEF catalogue response')
    return {'source': PORTAL + 'PortalWebDatasets/v1.0/getDatasets', 'query': keyword, 'requested_page': page, 'notes': NOTES, 'response': j}

def metadata(dataset):
    if not isinstance(dataset, str) or not re.fullmatch('[A-Za-z0-9_-]{1,160}', dataset):
        raise ValueError('Invalid dataset name')
    j = _post('PortalWebDatasetDetalle/v1.0/getDatasetDetalle', {'dataset': dataset})
    if j.get('status') != '0000' or not isinstance(j.get('resources'), list):
        raise ValueError('Dataset unavailable or unexpected metadata')
    return {'source': PORTAL + 'PortalWebDatasetDetalle/v1.0/getDatasetDetalle', 'notes': NOTES, 'response': j}

def records(resource_id, limit=10, offset=0):
    try:
        if not isinstance(resource_id, str) or str(uuid.UUID(resource_id)) != resource_id.lower():
            raise ValueError()
    except (ValueError, AttributeError):
        raise ValueError('Invalid resource UUID') from None
    if type(limit) is not int or not 1 <= limit <= 100 or type(offset) is not int or (not 0 <= offset <= 1000000):
        raise ValueError('Invalid limit or offset')
    r = requests.get(DATA, params={'resource_id': resource_id, 'limit': limit, 'offset': offset}, timeout=60)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, dict) or str(j.get('sucess')).lower() != 'true' or (not isinstance(j.get('records'), list)):
        raise ValueError('Unexpected MEF datastore response')
    return {'source': DATA, 'notes': NOTES, 'response': j}
