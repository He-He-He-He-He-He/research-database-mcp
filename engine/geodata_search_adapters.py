"""国家地球系统科学数据中心公开检索首屏；尚未接通详情。"""
import release_runtime
import requests
ENDPOINT = 'https://www.geodata.cn/service/scidata/entry/search/'
FIELDS = ('guid', 'docId', 'title', 'doi', 'cstr', 'keywords', 'description', 'disciplineName', 'ownerOrganization', 'placeName', 'dataStartTime', 'dataEndTime', 'dataTimeScale', 'dataTimeDescription', 'filesize', 'online', 'opened', 'createdTime', 'updatedTime')

def geodata_search(keyword, size=10):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100 or (not isinstance(size, int)) or (not 1 <= size <= 50):
        raise ValueError('请输入关键词，size 为 1–50')
    params = {'word': keyword, 'pageSize': size, 'page': 1, 'skip': 0, 'take': size}
    r = requests.get(ENDPOINT, params=params, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    raw = r.json().get('op_read')
    if not isinstance(raw, dict) or not isinstance(raw.get('data'), list):
        raise ValueError('未识别地球系统数据检索结果')
    return {'source': '国家地球系统科学数据中心', 'source_url': 'https://www.geodata.cn/data/', 'keyword': keyword, 'page': 1, 'total': raw.get('total'), 'items': [{k: row.get(k) for k in FIELDS} for row in raw['data']], 'note': '仅返回公开检索首屏的字段；详情尚未接通，时间戳及开放状态应核对原站。'}
