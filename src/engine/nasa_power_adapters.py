"""NASA POWER daily point data, UTC day, model/satellite grid estimates."""
import release_runtime
import datetime as dt
import json
import math
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://power.larc.nasa.gov/api/temporal/daily/point'

def daily(latitude, longitude, start, end, parameters='T2M,PRECTOTCORR', community='AG'):
    if isinstance(latitude, bool) or isinstance(longitude, bool) or (not isinstance(latitude, (int, float))) or (not isinstance(longitude, (int, float))) or (not math.isfinite(latitude)) or (not math.isfinite(longitude)) or (not -90 <= latitude <= 90) or (not -180 <= longitude <= 180):
        raise ValueError('invalid latitude or longitude')
    try:
        if not isinstance(start, str) or not isinstance(end, str):
            raise ValueError()
        s = dt.date.fromisoformat(start)
        e = dt.date.fromisoformat(end)
        if s.isoformat() != start or e.isoformat() != end:
            raise ValueError()
    except ValueError:
        raise ValueError('dates must be YYYY-MM-DD') from None
    if s < dt.date(1981, 1, 1) or e < s or (e - s).days > 365:
        raise ValueError('date range must start in 1981 or later and cover at most 366 days')
    if not isinstance(parameters, str) or not re.fullmatch('[A-Z][A-Z0-9_]*(?:,[A-Z][A-Z0-9_]*){0,14}', parameters) or len(set(parameters.split(','))) != len(parameters.split(',')):
        raise ValueError('provide 1–15 distinct NASA POWER parameter codes')
    if community not in ('AG', 'RE', 'SB'):
        raise ValueError('community must be AG, RE, or SB')
    names = parameters.split(',')
    p = {'parameters': parameters, 'community': community, 'longitude': longitude, 'latitude': latitude, 'start': s.strftime('%Y%m%d'), 'end': e.strftime('%Y%m%d'), 'format': 'JSON', 'time-standard': 'UTC'}
    url = BASE + '?' + urlencode(p)
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '35', url], capture_output=True, text=True, check=True)
    j = json.loads(r.stdout)
    h = j['header']
    values = j['properties']['parameter']
    meta = j['parameters']
    if h['time_standard'] != 'UTC' or h['start'] != p['start'] or h['end'] != p['end'] or any((k not in values or k not in meta for k in names)):
        raise ValueError('unexpected NASA response')
    dates = [(s + dt.timedelta(days=i)).strftime('%Y%m%d') for i in range((e - s).days + 1)]
    if any((set(values[k]) != set(dates) for k in names)):
        raise ValueError('incomplete date series')
    fill = h.get('fill_value')
    rows = []
    for day in dates:
        rows.append({'date': dt.datetime.strptime(day, '%Y%m%d').date().isoformat(), **{k: None if values[k][day] == fill else values[k][day] for k in names}})
    return {'source': 'NASA POWER Daily API', 'source_url': url, 'community': community, 'raw_parameter_values': values, 'time_standard': 'UTC', 'requested_point': {'latitude': latitude, 'longitude': longitude}, 'response_coordinates': j['geometry']['coordinates'], 'sources': h.get('sources'), 'parameters': meta, 'rows': rows, 'note': '格点卫星/模型估计，不是当地气象站实测；单位与变量定义以 parameters 元数据为准；缺测值保留在 raw_parameter_values，rows 中转为 null。'}
