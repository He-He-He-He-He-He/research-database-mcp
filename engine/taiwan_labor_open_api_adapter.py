"""Taiwan labor authority documented metadata and paginated resource API."""
import release_runtime
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://apiservice.mol.gov.tw/OdService/'

def _get(path, params=None):
    url = BASE + path + ('?' + urlencode(params) if params else '')
    result = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '30', '--', url], capture_output=True, check=True)
    return json.loads(result.stdout)

def datasets(limit=100, offset=0):
    if not 1 <= int(limit) <= 1000 or int(offset) < 0:
        raise ValueError('limit 应为 1–1000，offset 应为非负整数')
    return _get('rest/dataset', {'limit': int(limit), 'offset': int(offset)})

def metadata(dataset_id):
    if not re.fullmatch('\\d+', str(dataset_id)):
        raise ValueError('数据集编号必须为数字')
    return _get('rest/dataset/' + str(dataset_id))

def records(resource_id, limit=100, offset=0):
    if not re.fullmatch('[A-Za-z0-9-]{1,100}', str(resource_id)):
        raise ValueError('无效资源编号')
    if not 1 <= int(limit) <= 1000 or int(offset) < 0:
        raise ValueError('limit 应为 1–1000，offset 应为非负整数')
    result = _get('rest/datastore/' + resource_id, {'limit': int(limit), 'offset': int(offset)})
    if result.get('success') is not True:
        raise RuntimeError('数据来源返回失败')
    return result
