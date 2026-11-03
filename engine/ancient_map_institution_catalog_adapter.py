"""Reasonlib ancient-map catalog with institution IP validation."""
import release_runtime
import ast
import json
import requests
BASE = 'https://map.reasonlib.com/'
CLASS = {'Type': 'aid', 'Address': 'address', 'Organ': 'book_organ', 'Publisher': 'book_publisher', 'Cdgb': 'cdgb2'}

def search(keyword, page=1, limit=10, session=None, field='ALL', period_id=None, include_periods=False, class_id=None, include_classes=False):
    for ident in (period_id, class_id):
        if ident is not None and (type(ident) is not int or ident < 1):
            raise ValueError('分面 ID 须为正整数')
    if type(include_periods) is not bool or type(include_classes) is not bool:
        raise ValueError('分面开关须为布尔值')
    if period_id is not None and class_id is not None:
        raise ValueError('暂不支持类型与时期同时筛选')
    if field not in ('ALL', 'TI', 'AU', 'KW', 'NT', 'BI'):
        raise ValueError('不支持的检索字段')
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100:
        raise ValueError('关键词须为 1–100 字')
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('页码须为正整数')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 20):
        raise ValueError('每页最多 20 条')
    q = keyword.strip()
    s = session or requests.Session()
    s.get(BASE, timeout=20).raise_for_status()
    r = s.post(BASE + 'AjaxController.aspx/GetLoginIp', json={'ty': 'map'}, timeout=20)
    r.raise_for_status()
    try:
        ident = ast.literal_eval(r.json()['d'])
    except (KeyError, ValueError, SyntaxError, TypeError) as e:
        raise RuntimeError('机构身份响应异常') from e
    if not isinstance(ident, list) or len(ident) != 1 or (not isinstance(ident[0], dict)) or (str(ident[0].get('o')) != '1') or (ident[0].get('name') != '浙江大学'):
        raise RuntimeError('未确认浙江大学身份')
    body = {'ty': 'map', 'queryBody': {'searchValue': [{'sort': field, 'value': q}]}, 'pi': page, 'ps': limit, 'order': 'desc', 'ifyBody': '{}'}
    r = s.post(BASE + 'AjaxController.aspx/QueryGeneralRecords', json={'body': body, 'ifyBodyData': CLASS, 'Lang': 'false'}, timeout=20)
    r.raise_for_status()
    raw = r.json().get('d')
    if raw == '':
        raise RuntimeError('原站返回空响应，无法区分无结果或暂时异常')
    try:
        d = json.loads(raw)
        periods = []
        classes = []
        chosen_period = None
        chosen_class = None
        if period_id is not None or include_periods or class_id is not None or include_classes:
            facets = json.loads(d['ClassIfy'])

            def read_facet(key):
                out = []
                vals = json.loads(facets[key])
                if not isinstance(vals, list):
                    raise ValueError('invalid facet')
                for x in vals:
                    if not isinstance(x, dict) or type(x.get('id')) is not int or (not isinstance(x.get('name'), str)) or (not x['name'].strip()) or (type(x.get('count')) is not int) or (x['count'] < 0):
                        raise ValueError('invalid facet item')
                    out.append({'id': x['id'], 'name': x['name'], 'count': x['count']})
                return out
            if period_id is not None or include_periods:
                periods = read_facet('Cdgb')
            if class_id is not None or include_classes:
                classes = read_facet('Type')
        if period_id is not None or class_id is not None:
            candidates = periods if period_id is not None else classes
            selected_id = period_id if period_id is not None else class_id
            selected = [x for x in candidates if x['id'] == selected_id]
            if len(selected) != 1:
                raise ValueError('所选分面不在本次查询中')
            chosen_period = selected[0] if period_id is not None else None
            chosen_class = selected[0] if class_id is not None else None
            key = 'cdgb2' if chosen_period else 'aid'
            body['ifyBody'] = json.dumps({key: str(selected_id)}, ensure_ascii=False)
            selected_class = dict(CLASS)
            selected_class['Cdgb' if chosen_period else 'Type'] = '' if chosen_period else 'bid'
            r = s.post(BASE + 'AjaxController.aspx/QueryGeneralRecords', json={'body': body, 'ifyBodyData': selected_class, 'Lang': 'false'}, timeout=20)
            r.raise_for_status()
            raw = r.json().get('d')
            if raw == '':
                raise RuntimeError('原站返回空响应，无法区分无结果或暂时异常')
            d = json.loads(raw)
        rows = json.loads(d['PageData'])
        c = next((x for x in d['CityCount'] if x['Code'] == 'map'))
        total = int(c['Count'])
        if chosen_class and total != chosen_class['count']:
            raise ValueError('类型筛选总数与原分面不一致')
    except (ValueError, TypeError, KeyError, StopIteration) as e:
        raise RuntimeError('地图目录响应异常') from e
    if not isinstance(rows, list) or total < 0 or len(rows) > limit or (len(rows) > max(0, total - (page - 1) * limit)):
        raise RuntimeError('地图目录数量异常')
    items = []
    for x in rows:
        if not isinstance(x, dict) or type(x.get('id')) is not int or (not isinstance(x.get('name'), str)):
            raise RuntimeError('地图题录字段缺失')
        if chosen_period and (not isinstance(x.get('cdgb'), str) or chosen_period['name'] not in x['cdgb']):
            raise RuntimeError('结果时期与所选分面不符')
        items.append({'id': x['id'], 'guid': x.get('guid'), 'title': x['name'], 'author': x.get('auther'), 'year': x.get('year'), 'edition': x.get('edit'), 'period': x.get('cdgb'), 'address': x.get('address'), 'publisher': x.get('publisher'), 'holding_institution': x.get('organ')})
    result = {'source': '古地图库', 'institution': '浙江大学', 'trial': str(ident[0].get('state')) == '0', 'query': q, 'page': page, 'page_size': limit, 'record_count': total, 'map_count_display': c.get('Message'), 'items': items[:limit], 'note': '学校 IP 试用状态可能变化；记录数和站方显示地图张数分别保留，仅目录，影像权限未验证。'}
    if field != 'ALL':
        result['field_requested'] = field
        result['note'] += ' 按站方字段请求但响应未回显字段或页码；匹配可能涉及繁简异体，附注及简介只用于检索，不输出原文。'
    if include_periods:
        result['period_facets'] = periods
    if include_classes:
        result['class_facets'] = classes
    if chosen_period:
        result['period_filter'] = chosen_period
        result['note'] += ' 同会话核验时期选项并逐条核对返回时期。'
    if chosen_class:
        result['class_filter'] = chosen_class
        result['note'] += ' 类型筛选总数与原分面一致，来源不提供逐条类型编号。'
    if chosen_period or chosen_class:
        result['note'] += ' 站方未回显筛选和页码。'
    return result
