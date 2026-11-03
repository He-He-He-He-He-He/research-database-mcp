"""HBN IP-authenticated single-indicator table, preserving source fields and units."""
import release_runtime
import datetime
import re
import requests
from hbn_institution_indicator_adapter import BASE, _headers

def values(db_id, indicator_code, start_date, end_date, page=1, page_size=20, session=None):
    if not isinstance(db_id, str) or not re.fullmatch('[A-Za-z0-9_]{1,80}', db_id):
        raise ValueError('数据库标识无效')
    if not isinstance(indicator_code, str) or not re.fullmatch('[A-Za-z0-9_]{1,80}', indicator_code):
        raise ValueError('指标代码无效')
    try:
        a = datetime.date.fromisoformat(start_date)
        b = datetime.date.fromisoformat(end_date)
    except (TypeError, ValueError) as e:
        raise ValueError('日期须为 YYYY-MM-DD') from e
    if a.isoformat() != start_date or b.isoformat() != end_date or a > b:
        raise ValueError('日期范围无效')
    if not isinstance(page, int) or isinstance(page, bool) or page < 1 or (not isinstance(page_size, int)) or isinstance(page_size, bool) or (not 1 <= page_size <= 20):
        raise ValueError('分页参数无效')
    s = session or requests.Session()
    headers = _headers(s)
    r = s.post(BASE + 'db/dbShow/tbTagInfo', json={'dbId': db_id, 'tbId': indicator_code}, headers=headers, timeout=25)
    r.raise_for_status()
    j = r.json()
    meta = j.get('data') if isinstance(j, dict) else None
    if not isinstance(j, dict) or j.get('code') != 0 or (not isinstance(meta, list)) or (not any((isinstance(x, dict) and str(x.get('id')) == indicator_code for x in meta))):
        raise RuntimeError('指标定义或访问权限未确认')
    selected = next((x for x in meta if isinstance(x, dict) and str(x.get('id')) == indicator_code))
    body = {'pageNo': page - 1, 'pageSize': page_size, 'dbId': db_id, 'tableId': indicator_code, 'targets': indicator_code, 'timeId': '0', 'startDate': start_date, 'endDate': end_date, 'filterAdd': '', 'filterAnd': ''}
    r = s.post(BASE + 'db/dbShow/data', json=body, headers=headers, timeout=25)
    r.raise_for_status()
    j = r.json()
    d = j.get('data') if isinstance(j, dict) else None
    if not isinstance(j, dict) or j.get('code') != 0 or (not isinstance(d, dict)) or (d.get('pageNo') != page - 1) or (not isinstance(d.get('content'), list)):
        raise RuntimeError('指标数据响应异常或无权限')
    content = d['content']
    if len(content) > 1 or (content and (not isinstance(content[0], dict) or not isinstance(content[0].get('columns'), list) or (not isinstance(content[0].get('datas'), list)))):
        raise RuntimeError('数据表结构异常')
    cols = content[0]['columns'] if content else []
    rows = content[0]['datas'] if content else []
    if any((not isinstance(x, dict) for x in rows)) or len(rows) > page_size:
        raise RuntimeError('数据行异常')
    return {'source': 'HBN 环球财经数据库', 'institution': '浙江大学', 'db_id': db_id, 'indicator_code': indicator_code, 'indicator_name': selected.get('cnName'), 'unit': selected.get('unit'), 'indicator_type': selected.get('dataType'), 'source_info_raw': selected.get('infoSource'), 'indicator_metadata': selected, 'start_date': start_date, 'end_date': end_date, 'page': page, 'page_size': page_size, 'upstream_total': d.get('total'), 'columns': cols, 'rows': rows, 'note': '按原站字段和值返回单指标数据；来源为站方标注，单位与时间口径以指标定义为准；站方未明确实际值或预测值时，不可把未来年份当实绩，实际来源及修订须另核。'}
