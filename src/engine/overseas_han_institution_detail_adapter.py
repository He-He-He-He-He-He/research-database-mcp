"""域外汉籍库校园 IP 单册原始书目信息，不获取影像。"""
import release_runtime
import ast
import json
import re
import requests
from overseas_han_ip_catalog_adapter import BASE
GUID = re.compile('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.I)

def detail(guid, record_id, expected_title):
    if not isinstance(guid, str) or not GUID.fullmatch(guid):
        raise ValueError('书目 GUID 无效')
    if isinstance(record_id, bool) or not str(record_id).isdigit() or (not 1 <= int(record_id) <= 999999999999):
        raise ValueError('记录编号无效')
    if not isinstance(expected_title, str) or not expected_title.strip() or len(expected_title) > 300:
        raise ValueError('须提供完整书名')
    with requests.Session() as s:
        r = s.get(BASE, timeout=20)
        r.raise_for_status()
        r = s.post(BASE + 'AjaxController.aspx/GetLoginIp', json={'ty': 'book'}, timeout=20)
        r.raise_for_status()
        try:
            ident = ast.literal_eval(r.json()['d'])
        except (ValueError, SyntaxError, KeyError, TypeError):
            raise RuntimeError('机构认证响应异常') from None
        if not isinstance(ident, list) or len(ident) != 1 or (not isinstance(ident[0], dict)) or (str(ident[0].get('o')) != '1') or (ident[0].get('name') != '浙江大学'):
            raise RuntimeError('未确认浙江大学机构身份')
        r = s.post(BASE + 'ajax.aspx/GetInfo', json={'ty': 'book', 'id': guid, 'Lang': 'false'}, timeout=20)
        r.raise_for_status()
        try:
            data = json.loads(r.json()['d'])
        except (ValueError, KeyError, TypeError):
            raise RuntimeError('书目详情响应异常') from None
    if not isinstance(data, list) or len(data) != 1 or (not isinstance(data[0], dict)) or (str(data[0].get('id')) != str(record_id)) or (data[0].get('name') != expected_title.strip()):
        raise RuntimeError('书目编号或标题不匹配')
    return {'source': '域外汉籍库', 'institution': '浙江大学', 'trial': str(ident[0].get('state')) == '0', 'guid': guid, 'record': data[0], 'note': '站方原始单册书目，学校试用状态可能变化；未读取图像或验证逐书影像权限。'}
