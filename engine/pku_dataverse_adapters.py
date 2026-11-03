"""北京大学开放研究数据平台已发布数据集的公开元数据。"""
import release_runtime
import re
import requests
BASE = 'https://opendata.pku.edu.cn/api/'

def _get(path, params):
    r = requests.get(BASE + path, params=params, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    x = r.json()
    if x.get('status') != 'OK' or not isinstance(x.get('data'), dict):
        raise ValueError('未识别平台元数据')
    return x['data']

def pku_datasets(keyword, count=10, start=0):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100 or (not isinstance(count, int)) or (not 1 <= count <= 50) or (not isinstance(start, int)) or (start < 0):
        raise ValueError('请检查关键词及分页')
    x = _get('search', {'q': keyword, 'type': 'dataset', 'per_page': count, 'start': start})
    keys = ('name', 'type', 'url', 'global_id', 'description', 'published_at', 'name_of_dataverse', 'authors')
    return {'total': x.get('total_count'), 'start': x.get('start'), 'items': [{k: v for k, v in item.items() if k in keys} for item in x.get('items', [])]}

def pku_dataset_detail(doi):
    if not isinstance(doi, str):
        raise ValueError('请输入 DOI')
    doi = doi if doi.startswith('doi:') else 'doi:' + doi
    if not re.fullmatch('doi:10\\.18170/DVN/[A-Za-z0-9]{1,40}', doi, re.I):
        raise ValueError('仅支持北大平台 DOI')
    x = _get('datasets/:persistentId/versions/:latest', {'persistentId': doi})
    if x.get('versionState') != 'RELEASED':
        raise ValueError('未获得已发布版本')
    fields = x.get('metadataBlocks', {}).get('citation', {}).get('fields', [])
    keys = {'title', 'author', 'dsDescription', 'subject', 'keyword', 'dateOfDeposit', 'publication'}
    metadata = {a['typeName']: a.get('value') for a in fields if a.get('typeName') in keys}
    return {'doi': doi, 'version': x.get('versionNumber'), 'version_minor': x.get('versionMinorNumber'), 'release_time': x.get('releaseTime'), 'license': x.get('license'), 'terms_of_use': x.get('termsOfUse'), 'file_access_request': x.get('fileAccessRequest'), 'metadata': metadata}
