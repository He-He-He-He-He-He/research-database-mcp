"""古地图库校园 IP 单幅古地图原始著录，不获取影像。"""
import release_runtime
import ast
import json
import re
import requests
from ancient_map_institution_catalog_adapter import BASE
GUID = re.compile('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.I)

def detail(guid, record_id, expected_title):
    if not isinstance(guid, str) or not GUID.fullmatch(guid):
        raise ValueError('地图 GUID 无效')
    if isinstance(record_id, bool) or not str(record_id).isdigit() or (not 1 <= int(record_id) <= 999999999999):
        raise ValueError('记录编号无效')
    if not isinstance(expected_title, str) or not expected_title.strip() or len(expected_title) > 300:
        raise ValueError('须提供完整地图名称')
    with requests.Session() as s:
        r = s.get(BASE, timeout=20)
        r.raise_for_status()
        r = s.post(BASE + 'AjaxController.aspx/GetLoginIp', json={'ty': 'map'}, timeout=20)
        r.raise_for_status()
        try:
            ident = ast.literal_eval(r.json()['d'])
        except (ValueError, SyntaxError, KeyError, TypeError):
            raise RuntimeError('机构认证响应异常') from None
        if not isinstance(ident, list) or len(ident) != 1 or (not isinstance(ident[0], dict)) or (str(ident[0].get('o')) != '1') or (ident[0].get('name') != '浙江大学'):
            raise RuntimeError('未确认浙江大学机构身份')
        r = s.post(BASE + 'ajax.aspx/GetInfo', json={'ty': 'map', 'id': guid, 'Lang': 'false'}, timeout=20)
        r.raise_for_status()
        try:
            data = json.loads(r.json()['d'])
        except (ValueError, KeyError, TypeError):
            raise RuntimeError('地图详情响应异常') from None
    if not isinstance(data, list) or len(data) != 1 or (not isinstance(data[0], dict)) or (str(data[0].get('id')) != str(record_id)) or (data[0].get('Title') != expected_title.strip()):
        raise RuntimeError('地图编号或标题不匹配')
    return {'source': '古地图库', 'institution': '浙江大学', 'trial': str(ident[0].get('state')) == '0', 'guid': guid, 'record': data[0], 'note': '站方原始地图著录，含比例尺、材料、颜色等字段（可能缺失）；学校试用状态可能变化，未获取图像或确认影像权限。'}
