"""加拿大 ECCC 水文站、水位与流量历史及近实时官方数据。"""
import release_runtime
import requests
BASE = 'https://api.weather.gc.ca/collections/'
COLLECTIONS = {'stations': 'hydrometric-stations', 'daily': 'hydrometric-daily-mean', 'monthly': 'hydrometric-monthly-mean', 'realtime': 'hydrometric-realtime'}

def query(kind, station=None, datetime=None, limit=100, offset=0):
    if kind not in COLLECTIONS:
        raise ValueError('kind须为stations、daily、monthly或realtime')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 500):
        raise ValueError('limit须为1–500')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 0 <= offset <= 1000000):
        raise ValueError('offset无效')
    for x in (station, datetime):
        if x is not None and (not isinstance(x, str) or not 1 <= len(x) <= 100):
            raise ValueError('筛选参数无效')
    if kind != 'stations' and (not station):
        raise ValueError('观测须提供水文站编号')
    if kind == 'stations' and datetime:
        raise ValueError('站点目录不接受时间筛选')
    p = {'f': 'json', 'limit': limit, 'offset': offset}
    if station:
        p['STATION_NUMBER'] = station
    if datetime:
        p['datetime'] = datetime
    r = requests.get(BASE + COLLECTIONS[kind] + '/items', params=p, timeout=30)
    r.raise_for_status()
    d = r.json()
    if d.get('type') != 'FeatureCollection' or not isinstance(d.get('features'), list):
        raise ValueError('非预期 OGC 响应')
    return {'source': 'Environment and Climate Change Canada / Meteorological Service of Canada', 'source_url': r.url, 'kind': kind, 'numberMatched': d.get('numberMatched'), 'numberReturned': d.get('numberReturned'), 'features': d['features'], 'links': d.get('links', []), 'note': '水位基准、流量与质量标识以站点元数据和官方说明为准；null不是零。近实时数据可能未经最终审核；历史日均、月均与即时观测不可直接混同。'}
