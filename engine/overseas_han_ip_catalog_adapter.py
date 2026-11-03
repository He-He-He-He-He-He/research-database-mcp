"""Institution IP book catalog for 域外汉籍库; no images or full text."""
import release_runtime
import ast
import json
import requests
BASE = 'https://gj.reasonlib.com/'
CLASS = {'Type': 'aid', 'Address': 'address', 'Organ': 'book_organ', 'Publisher': 'book_publisher', 'Cdgb': 'cdgb2'}

def search(keyword, page=1, limit=10, session=None, field='ALL', period_id=None, include_periods=False, class_id=None, include_classes=False):
    if class_id is not None and (type(class_id) is not int or class_id < 1):
        raise ValueError('分类 ID 须为正整数')
    if type(include_classes) is not bool:
        raise ValueError('分类开关须为布尔值')
    if class_id is not None and period_id is not None:
        raise ValueError('暂不支持分类与时期同时筛选')
    if period_id is not None and (type(period_id) is not int or period_id < 1):
        raise ValueError('朝代国别 ID 须为正整数')
    if type(include_periods) is not bool:
        raise ValueError('分面开关须为布尔值')
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
    home = s.get(BASE, timeout=20)
    home.raise_for_status()
    login = s.post(BASE + 'AjaxController.aspx/GetLoginIp', json={'ty': 'book'}, timeout=20)
    login.raise_for_status()
    try:
        identity = ast.literal_eval(login.json()['d'])
    except (ValueError, SyntaxError, KeyError, TypeError) as e:
        raise RuntimeError('机构认证响应异常') from e
    if not isinstance(identity, list) or len(identity) != 1 or (not isinstance(identity[0], dict)) or (str(identity[0].get('o')) != '1') or (identity[0].get('name') != '浙江大学'):
        raise RuntimeError('未确认浙江大学机构身份')
    trial = str(identity[0].get('state')) == '0'
    body = {'ty': 'book', 'queryBody': {'searchValue': [{'sort': field, 'value': q}]}, 'pi': page, 'ps': limit, 'order': 'desc', 'ifyBody': '{}'}
    r = s.post(BASE + 'AjaxController.aspx/QueryGeneralRecords', json={'body': body, 'ifyBodyData': CLASS, 'Lang': 'false'}, timeout=20)
    r.raise_for_status()
    if r.json().get('d') == '':
        raise RuntimeError('原站返回空响应，无法区分无结果或暂时异常')
    try:
        d = json.loads(r.json()['d'])
        periods = []
        classes = []
        chosen_class = None
        if period_id is not None or include_periods or class_id is not None or include_classes:
            facets = json.loads(d['ClassIfy'])
        if class_id is not None or include_classes:
            raw_classes = json.loads(facets['Type'])
            if not isinstance(raw_classes, list):
                raise ValueError('invalid classes')
            for item in raw_classes:
                if not isinstance(item, dict) or type(item.get('id')) is not int or (not isinstance(item.get('name'), str)) or (not item['name'].strip()) or (type(item.get('count')) is not int) or (item['count'] < 0):
                    raise ValueError('invalid class')
                classes.append({'id': item['id'], 'name': item['name'], 'count': item['count']})
        if period_id is not None or include_periods:
            raw_periods = json.loads(facets['Cdgb'])
            if not isinstance(raw_periods, list):
                raise ValueError('invalid periods')
            for item in raw_periods:
                if not isinstance(item, dict) or type(item.get('id')) is not int or (not isinstance(item.get('name'), str)) or (not item['name'].strip()) or (type(item.get('count')) is not int) or (item['count'] < 0):
                    raise ValueError('invalid period')
                periods.append({'id': item['id'], 'name': item['name'], 'count': item['count']})
        selected = None
        if period_id is not None:
            selected = [x for x in periods if x['id'] == period_id]
            if len(selected) != 1:
                raise ValueError('所选朝代国别不在本次查询的分面中')
            selected = selected[0]
            body['ifyBody'] = json.dumps({'cdgb2': str(period_id)}, ensure_ascii=False)
            selected_class = dict(CLASS)
            selected_class['Cdgb'] = ''
            r = s.post(BASE + 'AjaxController.aspx/QueryGeneralRecords', json={'body': body, 'ifyBodyData': selected_class, 'Lang': 'false'}, timeout=20)
            r.raise_for_status()
            if r.json().get('d') == '':
                raise RuntimeError('原站返回空响应，无法区分无结果或暂时异常')
            d = json.loads(r.json()['d'])
        if class_id is not None:
            chosen = [x for x in classes if x['id'] == class_id]
            if len(chosen) != 1:
                raise ValueError('所选分类不在本次查询的分面中')
            chosen_class = chosen[0]
            body['ifyBody'] = json.dumps({'aid': str(class_id)}, ensure_ascii=False)
            selected_class = dict(CLASS)
            selected_class['Type'] = 'bid'
            r = s.post(BASE + 'AjaxController.aspx/QueryGeneralRecords', json={'body': body, 'ifyBodyData': selected_class, 'Lang': 'false'}, timeout=20)
            r.raise_for_status()
            if r.json().get('d') == '':
                raise RuntimeError('原站返回空响应，无法区分无结果或暂时异常')
            d = json.loads(r.json()['d'])
        rows = json.loads(d['PageData'])
        count = next((x['Count'] for x in d['CityCount'] if x['Code'] == 'book'))
        total = int(count)
        if chosen_class and total != chosen_class['count']:
            raise ValueError('筛选总数与原始分面不一致')
    except (ValueError, TypeError, KeyError, StopIteration) as e:
        raise RuntimeError('书目或分面响应异常') from e
    if not isinstance(rows, list) or total < 0 or len(rows) != min(limit, max(0, total - (page - 1) * limit)):
        raise RuntimeError('站方返回条数与总数及页码不一致，可能数据变化或响应不完整')
    items = []
    for x in rows:
        if not isinstance(x, dict) or type(x.get('id')) is not int or (not isinstance(x.get('name'), str)):
            raise RuntimeError('书目缺少编号或名称')
        if selected and (not isinstance(x.get('cdgb'), str) or selected['name'] not in x['cdgb']):
            raise RuntimeError('结果时期与所选分面不符')
        items.append({'id': x['id'], 'guid': x.get('guid'), 'title': x['name'], 'edition': x.get('edits'), 'period': x.get('cdgb')})
    result = {'source': '域外汉籍库', 'institution': '浙江大学', 'trial': trial, 'query': q, 'page': page, 'page_size': limit, 'total': total, 'items': items[:limit], 'note': '机构 IP 认证后全部字段书目检索；试用状态可能变化，此查询仅返回题录，逐项影像权限未验证。'}
    result['note'] += ' 已按书数和请求页次核对条数；站方未回显页码，数据可能变化，越界响应异常时保留错误。'
    if field != 'ALL':
        result['field_requested'] = field
        result['note'] = '机构 IP 会话字段限定题录检索；站方未回显请求字段及页码，可能涉及繁简异体或其他匹配；附注及简介仅用于检索，不输出正文。试用状态和逐项影像权限须另核。'
    if field != 'ALL':
        result['note'] += ' 已按书数和请求页次核对条数；数据可能变化，越界响应异常时保留错误。'
    if include_classes:
        result['class_facets'] = classes
    if chosen_class:
        result['class_filter'] = chosen_class
        result['note'] += ' 分类来自同次未筛选结果；已核对筛选总数与分面数量，结果未提供逐条分类 ID。'
    if include_periods:
        result['period_facets'] = periods
    if selected:
        result['period_filter'] = selected
        result['note'] += ' 分面来自同次未筛选结果，源未回显筛选/页码；已核对返回时期字段。'
    return result
