"""SciVal 作者或国家指标：按官方 ASJC 学科代码筛选。"""
import release_runtime
import math
import re
from elsevier_scival_official_adapter import _fetch, _text, AUTHOR_BASE, COUNTRY_BASE, COUNTRY_DOC, METRICS, RANGES

def query(kind, identifier, subjects, year_range='5yrs'):
    if kind not in ('author', 'country'):
        raise ValueError('kind 须为 author 或 country')
    if year_range not in RANGES:
        raise ValueError('不支持的年份范围')
    if not isinstance(subjects, str):
        raise ValueError('学科代码须为逗号分隔的字符串')
    codes = subjects.split(',')
    if not 1 <= len(codes) <= 5 or any((not re.fullmatch('\\d{2,4}', c) for c in codes)) or len(set(codes)) != len(codes):
        raise ValueError('提供 1–5 个不重复的 ASJC 数字代码，以英文逗号分隔')
    if kind == 'author':
        if not isinstance(identifier, str) or not re.fullmatch('[1-9][0-9]{0,15}', identifier):
            raise ValueError('作者 ID 须为正整数字符串')
        target_id = int(identifier)
        base = AUTHOR_BASE
        param = 'authors'
        doc = 'https://dev.elsevier.com/documentation/SciValAuthorAPI.wadl'
    else:
        if not isinstance(identifier, str) or not re.fullmatch('[A-Za-z]{3}', identifier):
            raise ValueError('国家或地区代码须为三个英文字母')
        code = identifier.upper()
        base = COUNTRY_BASE
        param = 'countryIds'
        doc = COUNTRY_DOC
        raw, key = _fetch('code/' + code, {}, COUNTRY_BASE)
        country = raw.get('country')
        if not isinstance(country, dict) or type(country.get('id')) is not int or country['id'] < 1 or (country.get('countryCode') != code):
            raise RuntimeError('SciVal 国家代码未获一致确认')
        target_id = country['id']
    params = {param: str(target_id), 'metricTypes': ','.join(METRICS), 'yearRange': year_range, 'byYear': 'true', 'includeSelfCitations': 'true', 'includedDocs': 'AllPublicationTypes', 'subjectAreaFilterURI': ','.join(('Class/ASJC/Code/' + c for c in codes))}
    raw, key = _fetch('metrics', params, base)
    src = raw.get('dataSource')
    res = raw.get('results')
    if not isinstance(src, dict) or not isinstance(res, list) or len(res) != 1 or (not isinstance(res[0], dict)):
        raise RuntimeError('SciVal 指标响应结构异常')
    entity = res[0].get(kind)
    if not isinstance(entity, dict) or type(entity.get('id')) is not int or entity['id'] != target_id:
        raise RuntimeError('SciVal 返回对象 ID 不一致')
    item = {'id': target_id, 'name': _text(entity.get('name'), key)}
    if kind == 'country':
        if entity.get('countryCode') != code:
            raise RuntimeError('SciVal 返回国家代码不一致')
        item['countryCode'] = code
    found = res[0].get('metrics')
    clean = []
    if not isinstance(found, list) or len(found) != len(METRICS):
        raise RuntimeError('SciVal 指标列表异常')
    for m in found:
        if not isinstance(m, dict) or m.get('metricType') not in METRICS or (not isinstance(m.get('valueByYear'), dict)):
            raise RuntimeError('SciVal 年度指标异常')
        v = m['valueByYear']
        if any((not isinstance(y, str) or not re.fullmatch('\\d{4}', y) or (n is not None and (type(n) not in (int, float) or not math.isfinite(n))) for y, n in v.items())):
            raise RuntimeError('SciVal 年度数值异常')
        clean.append({'metricType': m['metricType'], 'valueByYear': v})
    if {x['metricType'] for x in clean} != set(METRICS):
        raise RuntimeError('SciVal 指标类型不完整')
    source = {'sourceName': _text(src.get('sourceName'), key), 'lastUpdated': _text(src.get('lastUpdated'), key), 'metricStartYear': src.get('metricStartYear'), 'metricEndYear': src.get('metricEndYear')}
    if type(source['metricStartYear']) is not int or type(source['metricEndYear']) is not int:
        raise RuntimeError('SciVal 源年份异常')
    return {'source': 'Elsevier SciVal ' + kind.title() + ' Metrics API', 'documentation': doc, kind: item, 'dataSource': source, 'yearRange_requested': year_range, 'subject_codes_requested': codes, 'metrics': clean, 'includeSelfCitations': True, 'includedDocs': 'AllPublicationTypes', 'note': 'ASJC 多学科为 OR 匹配；学科可能重叠，不能将分类结果简单相加。源站不回显过滤条件，具体边界需核实；数据源为 Scopus 而非全部成果。作者须核对档案身份；年度被引数归年口径尚未核，不能视作当年新增全部引文。'}
