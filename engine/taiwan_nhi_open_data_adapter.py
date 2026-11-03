"""Taiwan health insurance open-data catalog and paged records."""
import release_runtime
import re
import requests
BASE = 'https://info.nhi.gov.tw/api/iode0010/v1/rest/'

def _id(value):
    if not re.fullmatch('[A-Za-z0-9-]{1,100}', str(value)):
        raise ValueError('无效数据集或资源编号')
    return str(value)

def datasets(limit=100, offset=0):
    if not 1 <= int(limit) <= 1000 or int(offset) < 0:
        raise ValueError('limit 需为 1–1000，offset 需非负')
    r = requests.get(BASE + 'dataset', params={'limit': int(limit), 'offset': int(offset)}, timeout=30)
    r.raise_for_status()
    return r.json()

def metadata(identifier):
    r = requests.get(BASE + 'dataset/' + _id(identifier), timeout=30)
    r.raise_for_status()
    try:
        return r.json()
    except ValueError:
        raise RuntimeError('来源未返回数据集元信息') from None

def records(resource_id, limit=100, offset=0):
    if not 1 <= int(limit) <= 1000 or int(offset) < 0:
        raise ValueError('limit 需为 1–1000，offset 需非负')
    r = requests.get(BASE + 'datastore/' + _id(resource_id), params={'limit': int(limit), 'offset': int(offset)}, headers={'User-Agent': 'Mozilla/5.0'}, timeout=40)
    r.raise_for_status()
    try:
        result = r.json()
    except ValueError:
        raise RuntimeError('数据源未提供此资源的查询接口') from None
    if result.get('success') is not True:
        raise RuntimeError('数据源返回失败')
    return result
