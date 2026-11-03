"""CAPMAS public website data services; preserve source observations verbatim."""
import release_runtime
import requests
BASE = 'https://www.capmas.gov.eg:8080/api/'

def _get(path, params=None):
    try:
        with requests.get(BASE + path, params=params, headers={'lo': 'en'}, timeout=35, stream=True, allow_redirects=False) as r:
            if r.is_redirect or not r.ok:
                raise RuntimeError('CAPMAS service returned HTTP ' + str(r.status_code))
            body = bytearray()
            for chunk in r.iter_content(65536):
                body.extend(chunk)
                if len(body) > 8000000:
                    raise RuntimeError('CAPMAS response exceeds 8 MB')
    except requests.RequestException as e:
        raise RuntimeError('CAPMAS request failed: ' + type(e).__name__) from None
    import json
    d = json.loads(body)
    if not isinstance(d, dict) or 'data' not in d or d.get('state') is False:
        raise RuntimeError('Unexpected CAPMAS response')
    return d['data']

def _id(v):
    if isinstance(v, bool) or not isinstance(v, int) or (not 1 <= v <= 10000000):
        raise ValueError('Use positive numeric CAPMAS identifier')
    return v

def subjects():
    d = _get('Subject/HasData')
    if not isinstance(d, list):
        raise RuntimeError('Unexpected CAPMAS subjects')
    return {'source': 'Egypt CAPMAS official subject directory', 'source_url': BASE + 'Subject/HasData', 'data': d, 'note': '官方阿拉伯语及英文翻译原样保留；目录项不保证全部有可用时间序列。'}

def subsubject(subject_id):
    _id(subject_id)
    d = _get('Subject/SubSubjectWithIndicator/' + str(subject_id))
    if not isinstance(d, dict) or not isinstance(d.get('publicationWithIndicators'), list):
        raise RuntimeError('Unexpected CAPMAS subsubject response')
    return {'source': 'Egypt CAPMAS official subject publication and indicator directory', 'source_url': BASE + 'Subject/SubSubjectWithIndicator/' + str(subject_id), 'data': d, 'note': '刊物 ID 与指标 ID 不同；保留英文及阿拉伯语名称。'}

def indicator(subject_id, publication_id, indicator_id, start_year=None, end_year=None):
    for x in (subject_id, publication_id, indicator_id):
        _id(x)
    for y in (start_year, end_year):
        if y is not None and (isinstance(y, bool) or not isinstance(y, int) or (not 1800 <= y <= 2200)):
            raise ValueError('Invalid year')
    if start_year is not None and end_year is not None and (start_year > end_year):
        raise ValueError('Invalid year interval')
    subject = subsubject(subject_id)['data']
    matches = []
    for pub in subject['publicationWithIndicators']:
        if pub.get('id') == publication_id:
            matches.extend((x for x in pub.get('indicators', []) if x.get('indicatorId') == indicator_id))
    if not matches:
        raise ValueError('Indicator is not listed under the specified subject and publication')
    detail = _get('Indicator/IndicatorDetails', {'indicatorId': indicator_id, 'publicationId': publication_id})
    if not isinstance(detail, dict) or detail.get('id') != indicator_id:
        raise RuntimeError('CAPMAS indicator detail mismatch')
    categories = _get('Indicator/IndicatorFilter', {'IndicatorId': indicator_id, 'SubSubjectId': subject_id})
    if not isinstance(categories, list):
        raise RuntimeError('Unexpected CAPMAS observations')
    result = []
    available_years = set()
    raw_count = 0
    selected_count = 0
    for category in categories:
        if not isinstance(category, dict) or not isinstance(category.get('data'), list):
            raise RuntimeError('Unexpected CAPMAS category')
        filtered = []
        for item in category['data']:
            if not isinstance(item, dict):
                raise RuntimeError('Unexpected CAPMAS observation')
            y = item.get('year')
            raw_count += 1
            if type(y) is int:
                available_years.add(y)
            if start_year is not None or end_year is not None:
                if not isinstance(y, int) or (start_year is not None and y < start_year) or (end_year is not None and y > end_year):
                    continue
            filtered.append(item)
            selected_count += 1
        result.append({**category, 'data': filtered})
    coverage = {'years_present': sorted(available_years), 'raw_observations': raw_count, 'selected_observations': selected_count, 'metadata_end_period': detail.get('endPeriod'), 'note': 'years_present 只表示至少一条记录的 year 字段，不保证各分类或该年的数据完整；元数据结束期可能晚于实际返回年份。'}
    groups = {}
    for category in result:
        name = category.get('name')
        if isinstance(name, str) and name.strip() and category['data']:
            key = ''.join(name.casefold().split())
            groups.setdefault(key, []).append({'id': category.get('id'), 'name': name})
    possible_duplicates = [items for items in groups.values() if len(items) > 1]
    return {'source': 'Egypt CAPMAS official website data', 'source_info': 'https://www.capmas.gov.eg/', 'subject_id': subject_id, 'publication_id': publication_id, 'indicator_id': indicator_id, 'indicator_metadata': detail, 'coverage': coverage, 'possible_duplicate_category_names': possible_duplicates, 'categories': result, 'note': '返回 API 原始数值、年份、季度、月份及空值，重复或异常不修正；possible_duplicate_category_names 只按名称忽略空白提示，未判定确为重复，须核原表，不可擅自合计。单位、周期、年份类型和说明以元数据及原刊物为准。观测端点按子主题和指标筛选，不包含出版物参数；所选刊物关联已核实但不能单凭接口证明各条值只属于该刊物。日期筛选仅本地按 year 字段；缺失不等于零，不能假设是当前或全国数据。'}
