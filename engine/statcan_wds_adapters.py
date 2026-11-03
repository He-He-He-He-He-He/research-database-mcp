"""Statistics Canada official WDS vector data and metadata."""
import release_runtime
import requests
BASE = 'https://www150.statcan.gc.ca/t1/wds/rest/'
GUIDE = 'https://www.statcan.gc.ca/en/developers/wds/user-guide'
LICENCE = 'https://www.statcan.gc.ca/en/terms-conditions/open-licence'

def vector(vector_id, latest=5):
    if isinstance(vector_id, bool) or not isinstance(vector_id, int) or vector_id < 1:
        raise ValueError('vector_id 必须为正整数')
    if isinstance(latest, bool) or not isinstance(latest, int) or (not 1 <= latest <= 100):
        raise ValueError('latest 必须为 1 至 100')
    s = requests.Session()

    def fetch(method, body):
        r = s.post(BASE + method, json=body, timeout=30)
        r.raise_for_status()
        value = r.json()
        if not isinstance(value, list) or len(value) != 1 or value[0].get('status') != 'SUCCESS' or (not isinstance(value[0].get('object'), dict)):
            raise RuntimeError('加拿大统计局 API 返回错误或异常结构')
        obj = value[0]['object']
        if obj.get('responseStatusCode') != 0 or obj.get('vectorId') != vector_id:
            raise RuntimeError('加拿大统计局返回的系列与请求不匹配')
        return obj
    metadata = fetch('getSeriesInfoFromVector', [{'vectorId': vector_id}])
    data = fetch('getDataFromVectorsAndLatestNPeriods', [{'vectorId': vector_id, 'latestN': latest}])
    if not isinstance(data.get('vectorDataPoint'), list):
        raise RuntimeError('未收到时间序列')
    r = s.post(BASE + 'getCubeMetadata', json=[{'productId': metadata['productId']}], timeout=30)
    r.raise_for_status()
    cube = r.json()
    if not isinstance(cube, list) or len(cube) != 1 or cube[0].get('status') != 'SUCCESS' or (not isinstance(cube[0].get('object'), dict)):
        raise RuntimeError('未收到统计表元数据')
    c = cube[0]['object']
    if str(c.get('productId')) != str(metadata['productId']):
        raise RuntimeError('统计表元数据与系列不匹配')
    table = {k: c.get(k) for k in ('productId', 'cubeTitleEn', 'cubeTitleFr', 'cubeStartDate', 'cubeEndDate', 'releaseTime')}
    return {'source': 'Statistics Canada Web Data Service', 'api_guide': GUIDE, 'licence': LICENCE, 'attribution': 'Statistics Canada', 'vector_id': vector_id, 'table': table, 'metadata': metadata, 'observations': data['vectorDataPoint'], 'note': '保留官方尺度、状态、保密与符号代码；引用时须注明来源，第三方材料可能另有许可。'}
