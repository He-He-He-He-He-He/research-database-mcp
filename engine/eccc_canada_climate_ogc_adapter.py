"""加拿大环境及气候变化部气候站及历史逐日、逐月、逐小时观测 OGC API。"""
import release_runtime
import requests
BASE = 'https://api.weather.gc.ca/collections/'
COLLECTIONS = {'stations': 'climate-stations', 'daily': 'climate-daily', 'monthly': 'climate-monthly', 'hourly': 'climate-hourly'}

def query(kind, station_id=None, station_name=None, province=None, datetime=None, limit=100, offset=0):
    if kind not in COLLECTIONS:
        raise ValueError('kind须为stations、daily、monthly或hourly')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 500):
        raise ValueError('limit须为1–500')
    if not isinstance(offset, int) or isinstance(offset, bool) or (not 0 <= offset <= 1000000):
        raise ValueError('offset无效')
    for x in (station_id, station_name, province, datetime):
        if x is not None and (not isinstance(x, str) or len(x) > 120):
            raise ValueError('筛选参数无效')
    if kind != 'stations' and station_name is not None:
        raise ValueError('站名筛选仅用于stations，请用station_id查询观测')
    if kind != 'stations' and province is not None:
        raise ValueError('省份筛选仅用于stations')
    params = {'f': 'json', 'limit': limit, 'offset': offset}
    if station_id:
        params['CLIMATE_IDENTIFIER'] = station_id
    if station_name:
        params['STATION_NAME'] = station_name
    if province:
        params['PROV_STATE_TERR_CODE'] = province
    if datetime:
        params['datetime'] = datetime
    url = BASE + COLLECTIONS[kind] + '/items'
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    d = r.json()
    if d.get('type') != 'FeatureCollection' or not isinstance(d.get('features'), list):
        raise ValueError('非预期OGC响应')
    return {'source': 'Environment and Climate Change Canada / Meteorological Service of Canada', 'source_url': r.url, 'kind': kind, 'numberMatched': d.get('numberMatched'), 'numberReturned': d.get('numberReturned'), 'features': d['features'], 'links': d.get('links', []), 'note': '原始站点观测及质量标识，单位与字段定义见官方集合元数据；空值并非零。站点查询为精确筛选，datetime按OGC格式指定；各站覆盖期不同。'}
