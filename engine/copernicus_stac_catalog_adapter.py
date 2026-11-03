"""Copernicus Data Space STAC 卫星遥感数据目录，匿名查询元数据。"""
import release_runtime
import math, re
import requests
BASE = 'https://stac.dataspace.copernicus.eu/v1/'

def collections():
    r = requests.get(BASE + 'collections', timeout=30)
    r.raise_for_status()
    d = r.json()
    if not isinstance(d.get('collections'), list):
        raise ValueError('非预期集合目录')
    return {'source': 'Copernicus Data Space Ecosystem', 'source_url': r.url, 'collections': d['collections'], 'note': '仅STAC当前纳入的集合，并非全部Copernicus数据。'}

def search(collection, bbox, datetime, limit=20):
    if not isinstance(collection, str) or not re.fullmatch('[a-zA-Z0-9][a-zA-Z0-9._-]{0,100}', collection):
        raise ValueError('无效集合ID')
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4 or any((isinstance(x, bool) or not isinstance(x, (float, int)) or (not math.isfinite(x)) for x in bbox)):
        raise ValueError('bbox须为西、南、东、北四个数字')
    w, s, e, n = bbox
    if not (-180 <= w < e <= 180 and -90 <= s < n <= 90):
        raise ValueError('bbox超出范围或顺序无效')
    if not isinstance(datetime, str) or not 1 <= len(datetime) <= 100:
        raise ValueError('datetime无效')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('limit须为1–100')
    p = {'collections': collection, 'bbox': ','.join(map(str, bbox)), 'datetime': datetime, 'limit': limit}
    r = requests.get(BASE + 'search', params=p, timeout=30)
    r.raise_for_status()
    d = r.json()
    if d.get('type') != 'FeatureCollection' or not isinstance(d.get('features'), list):
        raise ValueError('非预期STAC响应')
    return {'source': 'Copernicus Data Space Ecosystem', 'source_url': r.url, 'features': d['features'], 'links': d.get('links', []), 'context': d.get('context'), 'note': '返回遥感产品元数据与资产链接，不代表影像已下载；具体资产访问权限和认证以服务要求为准。坐标WGS84经纬度；bbox不支持跨反经线。'}
