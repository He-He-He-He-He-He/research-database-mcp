"""美国地质调查局 FDSN 全球地震目录。"""
import release_runtime
import argparse, datetime, json, math, re, subprocess
from urllib.parse import urlencode
URL = 'https://earthquake.usgs.gov/fdsnws/event/1/query'

def earthquakes(start, end, min_magnitude=5, limit=50, *, bbox=None, offset=1):
    for value in (start, end):
        if not isinstance(value, str) or not re.fullmatch('[0-9]{4}-[0-9]{2}-[0-9]{2}', value):
            raise ValueError('日期必须为 YYYY-MM-DD')
        try:
            datetime.date.fromisoformat(value)
        except (TypeError, ValueError) as exc:
            raise ValueError('日期必须为 YYYY-MM-DD') from exc
    if start > end:
        raise ValueError('开始日期不得晚于结束日期')
    if isinstance(min_magnitude, bool):
        raise ValueError('震级须为数字')
    if isinstance(limit, bool) or not (isinstance(limit, int) or (isinstance(limit, str) and limit.isascii() and limit.isdigit())):
        raise ValueError('结果数量须为整数')
    if not math.isfinite(float(min_magnitude)) or not -2 <= float(min_magnitude) <= 10 or (not 1 <= int(limit) <= 500):
        raise ValueError('震级或结果数量超出范围')
    if type(offset) is not int or offset < 1:
        raise ValueError('offset 为从 1 开始的正整数')
    if bbox is not None:
        if not isinstance(bbox, (tuple, list)) or len(bbox) != 4 or any((isinstance(v, bool) or not isinstance(v, (float, int)) or (not math.isfinite(v)) for v in bbox)):
            raise ValueError('bbox 须为西、南、东、北四个坐标')
        west, south, east, north = bbox
        if not -180 <= west < east <= 180 or not -90 <= south < north <= 90:
            raise ValueError('bbox 范围无效或跨日期变更线，请拆分查询')
    params = {'format': 'geojson', 'starttime': start, 'endtime': end, 'minmagnitude': float(min_magnitude), 'eventtype': 'earthquake', 'limit': int(limit), 'orderby': 'time', 'offset': offset}
    if bbox is not None:
        params.update({'minlongitude': west, 'minlatitude': south, 'maxlongitude': east, 'maxlatitude': north})
    url = URL + '?' + urlencode(params)
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '25', url], capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError('USGS 地震目录请求失败: ' + p.stderr.strip())
    d = json.loads(p.stdout)
    if d.get('type') != 'FeatureCollection' or not isinstance(d.get('features'), list):
        raise RuntimeError('USGS 地震目录响应结构异常')
    out = []
    for x in d['features']:
        a = x['properties']
        coords = x['geometry']['coordinates']
        out.append({'id': x['id'], 'magnitude': a.get('mag'), 'magnitude_type': a.get('magType'), 'place': a.get('place'), 'origin_time_ms_utc': a.get('time'), 'updated_ms_utc': a.get('updated'), 'status': a.get('status'), 'longitude': coords[0], 'latitude': coords[1], 'depth_km': coords[2], 'url': a.get('url')})
    return {'source': 'USGS FDSN Event Web Service', 'source_url': url, 'documentation': 'https://earthquake.usgs.gov/fdsnws/event/1/', 'scope': '全球 USGS 事件目录的地震，UTC 时间；结束日期为该日 00:00 UTC（含边界），并非整日末尾。默认按时间倒序，结果最多 limit 条，不代表符合条件的总数；震级和定位可修订，不用于地震预警；next_offset_candidate 仅为可能的下一页，并不保证存在。目录持续更新，按时间分页可能漏重。跨日期变更线应拆分区域。', 'count': len(out), 'offset': offset, 'next_offset_candidate': offset + len(out) if len(out) == int(limit) else None, 'items': out}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('start')
    p.add_argument('end')
    p.add_argument('--min-magnitude', type=float, default=5)
    p.add_argument('--limit', type=int, default=50)
    a = p.parse_args()
    print(json.dumps(earthquakes(a.start, a.end, a.min_magnitude, a.limit), ensure_ascii=False, indent=2))
