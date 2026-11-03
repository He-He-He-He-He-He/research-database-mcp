"""Discover IOM DTM admin1 codes from available assessment observations."""
import release_runtime
import iom_dtm_official_api_adapter as api

def areas(country, start, end, keyword='', limit=30, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 150 or type(limit) is not int or (not 1 <= limit <= 100) or (type(offset) is not int) or (not 0 <= offset <= 100000):
        raise ValueError('关键词或分页无效')
    result = api.observations('admin1', country, start, end)
    payload = result['data']
    rows = payload['result']
    total = payload.get('totalRecordsCount')
    if type(total) is not int or total != len(rows):
        raise RuntimeError('IOM 返回条数与总数不一致；请缩短时间范围')
    grouped = {}
    missing = 0
    for row in rows:
        if row.get('admin0Pcode') != country:
            raise RuntimeError('上游返回请求国家以外数据')
        code = row.get('admin1Pcode')
        name = row.get('admin1Name')
        if not isinstance(code, str) or not code or (not isinstance(name, str)) or (not name):
            missing += 1
            continue
        item = grouped.setdefault(code, {'admin1Pcode': code, 'names': set(), 'record_count': 0, 'reporting_dates': []})
        item['names'].add(name)
        item['record_count'] += 1
        if isinstance(row.get('reportingDate'), str):
            item['reporting_dates'].append(row['reportingDate'])
    items = []
    for x in grouped.values():
        dates = sorted(x.pop('reporting_dates'))
        x['names'] = sorted(x['names'])
        x['earliest_reporting_date'] = dates[0] if dates else None
        x['latest_reporting_date'] = dates[-1] if dates else None
        if keyword.casefold() in (x['admin1Pcode'] + ' ' + ' '.join(x['names'])).casefold():
            items.append(x)
    items.sort(key=lambda x: x['admin1Pcode'])
    return {'source': result['source'], 'parameters': result['parameters'], 'source_records': len(rows), 'records_missing_area': missing, 'matched_areas': len(items), 'offset': offset, 'items': items[offset:offset + limit], 'note': '一级地区代码从指定国家和日期的 IOM 评估记录中发现，非完整行政区划或全部历史覆盖；无记录不等于地区不存在。record_count 是评估记录数，不是人数；多轮、来源和时间不能直接相加。地区名保留所有变体，按代码可继续查询二级数据。'}
