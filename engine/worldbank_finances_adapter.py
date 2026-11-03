"""World Bank Finances One public dataset metadata and paginated records.

Dataset and resource identifiers come from each dataset's API Explorer. The
record endpoint returns the latest snapshot unless the selected dataset says
otherwise. Consult metadata column_details and license before interpreting it.
"""
import release_runtime
import re
import requests
BASE = 'https://datacatalogapi.worldbank.org/dexapps/fone/api/'
EXAMPLES = {'ida_credits_grants_guarantees': ('DS00001', 'RS00001'), 'ibrd_loans': ('DS00047', 'RS00049')}

def _id(value, prefix):
    if not isinstance(value, str) or not re.fullmatch(prefix + '\\d+', value):
        raise ValueError(f'Expected a {prefix} identifier followed by digits')
    return value

def _get(endpoint, params):
    response = requests.get(BASE + endpoint, params=params, timeout=30)
    response.raise_for_status()
    return response.json()

def metadata(dataset_id):
    """Return official dataset description, field definitions and license."""
    return _get('metadata', {'assetId': _id(dataset_id, 'DS')})

def records(dataset_id, resource_id, top=100, skip=0):
    """Fetch one page; count is the upstream total, not the page length."""
    _id(dataset_id, 'DS')
    _id(resource_id, 'RS')
    if isinstance(top, bool) or not isinstance(top, int) or (not 1 <= top <= 1000):
        raise ValueError('top must be an integer from 1 to 1000')
    if isinstance(skip, bool) or not isinstance(skip, int) or skip < 0:
        raise ValueError('skip must be a nonnegative integer')
    result = _get('apiservice', {'datasetId': dataset_id, 'resourceId': resource_id, 'top': top, 'skip': skip, 'type': 'json'})
    if not isinstance(result, dict) or not isinstance(result.get('data'), list) or type(result.get('count')) is not int or (result['count'] < 0):
        raise ValueError('unexpected Finances One records response')
    if len(result['data']) > min(top, max(0, result['count'] - skip)):
        raise ValueError('Finances One records contradict pagination')
    return {**result, 'toolkit_request': {'dataset_id': dataset_id, 'resource_id': resource_id, 'top': top, 'skip': skip}, 'toolkit_note': 'resource_id 未经验证：实测部分数据集传入不同 resourceId 仍返回相同数据；请核对数据集元数据和 API Explorer，不要据此认定资源编号有效。count 是上游数据集总数。'}
