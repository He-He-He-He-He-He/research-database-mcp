"""NOAA 美国国家气象局公共天气 API：坐标、站点与预报。"""
import release_runtime
import argparse
import json
import math
import re
import subprocess
from urllib.parse import urlsplit
BASE = 'https://api.weather.gov'
MAX_BYTES = 5000000

def _get(path):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', '--max-filesize', str(MAX_BYTES), '-H', 'User-Agent: zju-research-toolkit/1.0', '-H', 'Accept: application/geo+json', BASE + path], capture_output=True, timeout=30)
    if p.returncode:
        raise RuntimeError('NWS 请求失败：' + p.stderr.decode('utf-8', 'replace')[:500])
    if len(p.stdout) > MAX_BYTES:
        raise ValueError('响应超过大小上限')
    value = json.loads(p.stdout)
    if not isinstance(value, dict):
        raise ValueError('响应不是预期的 JSON 对象')
    return value

def _point(lat, lon):
    for val, bound in ((lat, 90), (lon, 180)):
        if isinstance(val, bool) or not isinstance(val, (float, int)) or (not math.isfinite(val)) or (abs(val) > bound):
            raise ValueError('无效经纬度')
    return f'{lat:.4f},{lon:.4f}'

def point(lat, lon):
    path = '/points/' + _point(lat, lon)
    out = _get(path)
    if not isinstance(out.get('properties'), dict):
        raise ValueError('未识别点位信息')
    return {'source': BASE + path, 'data': out, 'note': '预报网格会改变；覆盖范围和当前数据以 NWS 为准。'}

def _safe_url(url, pattern):
    p = urlsplit(url)
    if p.scheme != 'https' or p.netloc != 'api.weather.gov' or p.query or p.fragment or (not re.fullmatch(pattern, p.path)):
        raise ValueError('上游返回了不支持的地址')
    return p.path

def forecast(lat, lon, hourly=False):
    if not isinstance(hourly, bool):
        raise ValueError('hourly 须为布尔值')
    props = point(lat, lon)['data']['properties']
    name = 'forecastHourly' if hourly else 'forecast'
    path = _safe_url(props.get(name, ''), '/gridpoints/[A-Z]{3}/\\d+,\\d+/forecast(?:/hourly)?')
    data = _get(path)
    if not isinstance(data.get('properties', {}).get('periods'), list):
        raise ValueError('未识别预报时段')
    return {'source': BASE + path, 'data': data, 'note': '预报不是观测数据；时间、温度单位及更新时点以原始字段为准。'}

def stations(lat, lon):
    url = point(lat, lon)['data']['properties'].get('observationStations', '')
    path = _safe_url(url, '/gridpoints/[A-Z]{3}/\\d+,\\d+/stations')
    data = _get(path)
    if not isinstance(data.get('features'), list):
        raise ValueError('未识别站点列表')
    return {'source': BASE + path, 'data': data, 'note': '站点按距离预测网格远近排列，不保证该站拥有实时观测。'}

def observation(station):
    if not isinstance(station, str) or not re.fullmatch('[A-Z0-9]{3,8}', station):
        raise ValueError('站点代码无效')
    path = '/stations/' + station + '/observations/latest'
    data = _get(path)
    if not isinstance(data.get('properties'), dict):
        raise ValueError('未识别站点观测')
    return {'source': BASE + path, 'data': data, 'note': '站点最近一次观测可能延迟或缺失，保留原始时间、单位及质量标记；不是长期气候统计。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    for name in ('point', 'forecast', 'stations'):
        q = s.add_parser(name)
        q.add_argument('latitude', type=float)
        q.add_argument('longitude', type=float)
        if name == 'forecast':
            q.add_argument('--hourly', action='store_true')
    q = s.add_parser('observation')
    q.add_argument('station')
    a = p.parse_args()
    if a.cmd == 'observation':
        value = observation(a.station)
    elif a.cmd == 'point':
        value = point(a.latitude, a.longitude)
    elif a.cmd == 'stations':
        value = stations(a.latitude, a.longitude)
    else:
        value = forecast(a.latitude, a.longitude, a.hourly)
    print(json.dumps(value, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
