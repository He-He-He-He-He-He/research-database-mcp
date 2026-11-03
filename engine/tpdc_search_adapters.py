"""国家青藏高原科学数据中心公开数据集搜索。"""
import release_runtime
import requests
from tpdc_catalog_adapters import tpdc_catalog_detail
URL = 'https://www.tpdc.ac.cn/view/metadataView/page'
FIELDS = ('id', 'title', 'description', 'doi', 'size', 'fileSize', 'tsCreated', 'tsUpdated', 'authorName', 'sharePolicy', 'status', 'protectedDuration')

def tpdc_search(keyword, page=1, size=10):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100 or (not isinstance(page, int)) or (not 1 <= page <= 100) or (not isinstance(size, int)) or (not 1 <= size <= 50):
        raise ValueError('检查关键词与分页')
    body = {'title': keyword, 'daid': '', 'pageSize': size, 'pageNum': page, 'downloadSort': False, 'viewsSort': False, 'tsUpdateTimeSort': True, 'placeId': '', 'subjectId': '', 'themeId': '', 'isImportant': False, 'isEnglish': False}
    r = requests.post(URL, json=body, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    x = r.json()
    if str(x.get('code')) != '200':
        raise ValueError('上游未返回成功')
    data = x.get('context', {}).get('metadataViewVOPage', {})
    if not isinstance(data.get('records'), list):
        raise ValueError('未识别数据集搜索结果')
    return {'total': data.get('total'), 'page': page, 'items': [{k: v for k, v in a.items() if k in FIELDS} for a in data['records']], 'note': '上游数据集搜索；分享策略和状态字段原样返回，具体许可与文件获取以数据集原页为准。'}

def tpdc_search_detail(identifier):
    return tpdc_catalog_detail(identifier)
