"""WorldPop Global2 modeled population within a user-specified bounding box."""
import release_runtime
import math, re
import requests
BASE = 'https://api.worldpop.org/v2'
HEADERS = {'Accept': 'application/json', 'User-Agent': 'PersonalResearchToolkit/1.0'}
NOTE = 'WorldPop 栅格模型估计并非人口普查实数；未来年份属于模型估计。小区域、网格分辨率、边界和模型不确定性会影响结果，不要把小数强作真实人数。'

def submit_bbox(west, south, east, north, year, resolution='1km', session=None):
    values = (west, south, east, north)
    if any((type(x) not in (int, float) or not math.isfinite(x) for x in values)) or not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError('经纬度矩形边界无效；不支持跨日期变更线')
    if type(year) is not int or not 2015 <= year <= 2030 or resolution not in ('1km', '100m'):
        raise ValueError('年份应为 2015–2030，分辨率应为 1km 或 100m')
    coords = [[[west, south], [east, south], [east, north], [west, north], [west, south]]]
    payload = {'geojson': {'type': 'Polygon', 'coordinates': coords}, 'year': year, 'resolution': resolution}
    r = (session or requests).post(BASE + '/population', json=payload, headers=HEADERS, timeout=25)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, dict) or not isinstance(data.get('task_id'), str) or (not re.fullmatch('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', data['task_id'], re.I)):
        raise ValueError('WorldPop 未返回有效任务编号')
    return {'source': 'WorldPop Global2 / University of Southampton', 'source_url': 'https://api.worldpop.org/v2/', 'input': payload, 'note': NOTE, 'data': data, 'poll_url': BASE + '/tasks/' + data['task_id']}

def task(task_id, session=None):
    if not isinstance(task_id, str) or not re.fullmatch('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', task_id, re.I):
        raise ValueError('WorldPop 任务编号格式无效')
    url = BASE + '/tasks/' + task_id
    r = (session or requests).get(url, headers=HEADERS, timeout=25)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, dict) or data.get('task_id') != task_id or data.get('status') not in ('pending', 'started', 'processing', 'success', 'failure'):
        raise ValueError('WorldPop 任务状态异常')
    return {'source': 'WorldPop Global2 / University of Southampton', 'source_url': url, 'note': NOTE, 'data': data}
