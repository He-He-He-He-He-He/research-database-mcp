"""Elsevier SciVal 官方机构和逐年指标；严格移除带密钥的站方链接。"""
import release_runtime
import math
import re
import requests
from elsevier_sciencedirect_search_adapter import _key
BASE = 'https://api.elsevier.com/analytics/scival/institution/'
AUTHOR_BASE = 'https://api.elsevier.com/analytics/scival/author/'
SUBJECT_BASE = 'https://api.elsevier.com/analytics/scival/subjectArea/'
DOC = 'https://dev.elsevier.com/documentation/SciValInstitutionAPI.wadl'
METRICS = ('ScholarlyOutput', 'CitationCount', 'FieldWeightedCitationImpact')
RANGES = ('3yrs', '3yrsAndCurrent', '3yrsAndCurrentAndFuture', '5yrs', '5yrsAndCurrent', '5yrsAndCurrentAndFuture', '10yrs')

def _fetch(path, params, base=BASE):
    key = _key()
    try:
        r = requests.get(base + path, params=params, headers={'X-ELS-APIKey': key, 'Accept': 'application/json'}, timeout=30)
    except requests.RequestException as e:
        raise RuntimeError('SciVal 请求失败：' + type(e).__name__) from None
    if r.status_code != 200:
        raise RuntimeError('SciVal 接口返回 HTTP ' + str(r.status_code) + '；不能据此判断学校权限或机构是否存在')
    try:
        o = r.json()
    except ValueError:
        raise RuntimeError('SciVal 接口未返回 JSON') from None
    if not isinstance(o, dict):
        raise RuntimeError('SciVal 响应结构异常')
    return (o, key)

def _text(value, key):
    if not isinstance(value, str) or key in value or len(value) > 500 or re.search('[\\x00-\\x1f]', value):
        raise RuntimeError('SciVal 返回文字字段异常')
    return value

def _institution(x, key):
    if not isinstance(x, dict) or type(x.get('id')) is not int or x['id'] < 1:
        raise RuntimeError('SciVal 机构 ID 异常')
    return {'id': x['id'], 'name': _text(x.get('name'), key), 'country': _text(x.get('country'), key), 'countryCode': _text(x.get('countryCode'), key)}

def search(name, limit=10):
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 120 or re.search('[()\\x00-\\x1f]', name):
        raise ValueError('机构名称须为 1–120 字单行文本，不接受括号')
    if type(limit) is not int or not 1 <= limit <= 50:
        raise ValueError('limit 须为 1–50')
    o, key = _fetch('search', {'query': 'name(' + name.strip() + ')'})
    if 'results' not in o:
        return {'source': 'Elsevier SciVal Institution API', 'documentation': DOC, 'query': name.strip(), 'returned_count': None, 'items': [], 'note': '源站响应未包含 results 字段，不能据此确认无匹配或服务完整。'}
    items = o['results']
    if items is None:
        items = []
    if not isinstance(items, list):
        raise RuntimeError('SciVal 机构列表异常')
    clean = [_institution(x, key) for x in items]
    return {'source': 'Elsevier SciVal Institution API', 'documentation': DOC, 'query': name.strip(), 'returned_count': len(clean), 'items': clean[:limit], 'note': '仅表示本次响应收到的机构数，未核实上游有无其他页或数量上限，且结果顺序可能变化；名称相似须按 SciVal ID 和机构核对，不能等同 Scopus Affiliation ID，也不证明机构现有订购权。'}

def metrics(institution_id, year_range='5yrs', subject_code=''):
    if not isinstance(institution_id, str) or not re.fullmatch('[1-9][0-9]{0,11}', institution_id):
        raise ValueError('SciVal 机构 ID 须为正整数字符串')
    if year_range not in RANGES:
        raise ValueError('不支持的年份范围')
    if not isinstance(subject_code, str) or (subject_code and (not re.fullmatch('\\d{2,4}', subject_code))):
        raise ValueError('ASJC 学科代码须为 2–4 位数字')
    params = {'institutionIds': institution_id, 'metricTypes': ','.join(METRICS), 'yearRange': year_range, 'byYear': 'true', 'includeSelfCitations': 'true', 'includedDocs': 'AllPublicationTypes'}
    if subject_code:
        params['subjectAreaFilterURI'] = 'Class/ASJC/Code/' + subject_code
    o, key = _fetch('metrics', params)
    src = o.get('dataSource')
    res = o.get('results')
    if not isinstance(src, dict) or not isinstance(res, list) or len(res) != 1 or (not isinstance(res[0], dict)):
        raise RuntimeError('SciVal 指标响应结构异常')
    inst = _institution(res[0].get('institution'), key)
    if inst['id'] != int(institution_id):
        raise RuntimeError('SciVal 返回机构 ID 与请求不一致')
    raw = res[0].get('metrics')
    clean = []
    if not isinstance(raw, list) or len(raw) != len(METRICS):
        raise RuntimeError('SciVal 指标列表异常')
    for m in raw:
        if not isinstance(m, dict) or m.get('metricType') not in METRICS or (not isinstance(m.get('valueByYear'), dict)):
            raise RuntimeError('SciVal 年度指标结构异常')
        vals = m['valueByYear']
        if any((not isinstance(y, str) or not re.fullmatch('\\d{4}', y) or (v is not None and (type(v) not in (int, float) or not math.isfinite(v))) for y, v in vals.items())):
            raise RuntimeError('SciVal 年度指标数值异常')
        clean.append({'metricType': m['metricType'], 'valueByYear': vals})
    if {x['metricType'] for x in clean} != set(METRICS):
        raise RuntimeError('SciVal 指标类型不完整')
    source = {'sourceName': _text(src.get('sourceName'), key), 'lastUpdated': _text(src.get('lastUpdated'), key), 'metricStartYear': src.get('metricStartYear'), 'metricEndYear': src.get('metricEndYear')}
    if type(source['metricStartYear']) is not int or type(source['metricEndYear']) is not int:
        raise RuntimeError('SciVal 源数据年份异常')
    return {'source': 'Elsevier SciVal Institution Metrics API', 'documentation': DOC, 'institution': inst, 'dataSource': source, 'yearRange_requested': year_range, 'subject_code_requested': subject_code or None, 'byYear': True, 'includeSelfCitations': True, 'includedDocs': 'AllPublicationTypes', 'metrics': clean, 'note': 'Scopus 数据的 SciVal 年度原值：ScholarlyOutput 是学术产出篇数，CitationCount 是所选作品被引次数，FieldWeightedCitationImpact 是学科加权引用影响力（无量纲）；年度被引数的具体归年口径需另核实，不应直接视为当年发生的全部引文。若按 ASJC 分类筛选，源站未回显请求条件，指标的具体分类边界需按其说明核对；学科间可能重叠。来源更新与覆盖年份按响应为准，自引设置仅对适用指标生效。指标受索引、统计口径、年份与版本影响，不等同学校全部成果。'}

def subject_areas(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100 or re.search('[\\x00-\\x1f]', keyword):
        raise ValueError('关键词须为不超过 100 字的单行文本')
    o, key = _fetch('classificationType/ASJC', {}, SUBJECT_BASE)
    areas = o.get('subjectAreas')
    if not isinstance(areas, list) or len(areas) > 100:
        raise RuntimeError('SciVal ASJC 分类响应异常')

    def item(x):
        if not isinstance(x, dict) or type(x.get('id')) is not int or x.get('classificationType') != 'ASJC' or (x.get('uri') != 'Class/ASJC/Code/' + str(x['id'])):
            raise RuntimeError('SciVal ASJC 分类代码异常')
        return {'code': str(x['id']), 'name': _text(x.get('name'), key)}
    clean = []
    for a in areas:
        top = item(a)
        children = a.get('children', [])
        if not isinstance(children, list) or len(children) > 100:
            raise RuntimeError('SciVal ASJC 子分类异常')
        subs = [item(c) for c in children]
        if keyword.strip() and keyword.casefold().strip() not in top['name'].casefold():
            subs = [c for c in subs if keyword.casefold().strip() in c['name'].casefold()]
            if not subs:
                continue
        top['children'] = subs
        clean.append(top)
    return {'source': 'Elsevier SciVal ASJC Subject Area API', 'documentation': 'https://dev.elsevier.com/documentation/SciValSubjectAreaAPI.wadl', 'keyword': keyword.strip(), 'items': clean, 'note': '按站方 ASJC 顶级分类及一级子类原始名称和代码返回，关键词仅在本机过滤；并非其他分类体系。学科可重叠，不应简单相加。'}

def author_metrics(author_id, year_range='5yrs'):
    if not isinstance(author_id, str) or not re.fullmatch('[1-9][0-9]{0,15}', author_id):
        raise ValueError('Scopus 作者 ID 须为正整数字符串')
    if year_range not in RANGES:
        raise ValueError('不支持的年份范围')
    params = {'authors': author_id, 'metricTypes': ','.join(METRICS), 'yearRange': year_range, 'byYear': 'true', 'includeSelfCitations': 'true', 'includedDocs': 'AllPublicationTypes'}
    o, key = _fetch('metrics', params, AUTHOR_BASE)
    src = o.get('dataSource')
    res = o.get('results')
    if not isinstance(src, dict) or not isinstance(res, list) or len(res) != 1 or (not isinstance(res[0], dict)):
        raise RuntimeError('SciVal 作者指标响应结构异常')
    author = res[0].get('author')
    if not isinstance(author, dict) or type(author.get('id')) is not int or author['id'] != int(author_id):
        raise RuntimeError('SciVal 返回作者 ID 与请求不一致')
    author = {'id': author['id'], 'name': _text(author.get('name'), key)}
    raw = res[0].get('metrics')
    clean = []
    if not isinstance(raw, list) or len(raw) != len(METRICS):
        raise RuntimeError('SciVal 作者指标列表异常')
    for m in raw:
        if not isinstance(m, dict) or m.get('metricType') not in METRICS or (not isinstance(m.get('valueByYear'), dict)):
            raise RuntimeError('SciVal 作者年度指标结构异常')
        vals = m['valueByYear']
        if any((not isinstance(y, str) or not re.fullmatch('\\d{4}', y) or (v is not None and (type(v) not in (int, float) or not math.isfinite(v))) for y, v in vals.items())):
            raise RuntimeError('SciVal 作者年度指标数值异常')
        clean.append({'metricType': m['metricType'], 'valueByYear': vals})
    if {x['metricType'] for x in clean} != set(METRICS):
        raise RuntimeError('SciVal 作者指标类型不完整')
    source = {'sourceName': _text(src.get('sourceName'), key), 'lastUpdated': _text(src.get('lastUpdated'), key), 'metricStartYear': src.get('metricStartYear'), 'metricEndYear': src.get('metricEndYear')}
    if type(source['metricStartYear']) is not int or type(source['metricEndYear']) is not int:
        raise RuntimeError('SciVal 源数据年份异常')
    return {'source': 'Elsevier SciVal Author Metrics API', 'documentation': 'https://dev.elsevier.com/documentation/SciValAuthorAPI.wadl', 'author': author, 'dataSource': source, 'yearRange_requested': year_range, 'byYear': True, 'includeSelfCitations': True, 'includedDocs': 'AllPublicationTypes', 'metrics': clean, 'note': '作者为 Scopus 档案，姓名相似或 ID 存在不证明与特定个人身份一致；须结合机构和论文核对。年度学术产出篇数、作品被引数和无量纲学科加权引用影响力按源站原值返回；年度被引数的归年口径尚未核实，不应视为当年全部新发生引文。来源更新与覆盖年份按响应为准，自引设置仅对适用指标生效；不代表该作者全部成果。'}
COUNTRY_BASE = 'https://api.elsevier.com/analytics/scival/country/'
COUNTRY_DOC = 'https://dev.elsevier.com/documentation/SciValCountryAPI.wadl'

def country_metrics(country_code, year_range='5yrs'):
    if not isinstance(country_code, str) or not re.fullmatch('[A-Za-z]{3}', country_code):
        raise ValueError('国家或地区代码须为三位英文字母')
    if year_range not in RANGES:
        raise ValueError('不支持的年份范围')
    code = country_code.upper()
    o, key = _fetch('code/' + code, {}, COUNTRY_BASE)
    country = o.get('country')
    if not isinstance(country, dict) or type(country.get('id')) is not int or country['id'] < 1 or (country.get('countryCode') != code):
        raise RuntimeError('SciVal 国家或地区代码未获一致确认')
    cid = country['id']
    name = _text(country.get('name'), key)
    params = {'countryIds': str(cid), 'metricTypes': ','.join(METRICS), 'yearRange': year_range, 'byYear': 'true', 'includeSelfCitations': 'true', 'includedDocs': 'AllPublicationTypes'}
    o, key = _fetch('metrics', params, COUNTRY_BASE)
    src = o.get('dataSource')
    res = o.get('results')
    if not isinstance(src, dict) or not isinstance(res, list) or len(res) != 1 or (not isinstance(res[0], dict)):
        raise RuntimeError('SciVal 国家或地区指标响应结构异常')
    found = res[0].get('country')
    if not isinstance(found, dict) or type(found.get('id')) is not int or found['id'] != cid or (found.get('countryCode') != code) or (found.get('name') != name):
        raise RuntimeError('SciVal 指标响应的国家或地区不一致')
    raw = res[0].get('metrics')
    clean = []
    if not isinstance(raw, list) or len(raw) != len(METRICS):
        raise RuntimeError('SciVal 国家或地区指标列表异常')
    for m in raw:
        if not isinstance(m, dict) or m.get('metricType') not in METRICS or (not isinstance(m.get('valueByYear'), dict)):
            raise RuntimeError('SciVal 年度指标结构异常')
        vals = m['valueByYear']
        if any((not isinstance(y, str) or not re.fullmatch('\\d{4}', y) or (v is not None and (type(v) not in (int, float) or not math.isfinite(v))) for y, v in vals.items())):
            raise RuntimeError('SciVal 年度指标数值异常')
        clean.append({'metricType': m['metricType'], 'valueByYear': vals})
    if {x['metricType'] for x in clean} != set(METRICS):
        raise RuntimeError('SciVal 国家或地区指标类型不完整')
    source = {'sourceName': _text(src.get('sourceName'), key), 'lastUpdated': _text(src.get('lastUpdated'), key), 'metricStartYear': src.get('metricStartYear'), 'metricEndYear': src.get('metricEndYear')}
    if type(source['metricStartYear']) is not int or type(source['metricEndYear']) is not int:
        raise RuntimeError('SciVal 源数据年份异常')
    return {'source': 'Elsevier SciVal Country Metrics API', 'documentation': COUNTRY_DOC, 'country': {'id': cid, 'name': name, 'countryCode': code}, 'dataSource': source, 'yearRange_requested': year_range, 'byYear': True, 'includeSelfCitations': True, 'includedDocs': 'AllPublicationTypes', 'metrics': clean, 'note': 'SciVal 基于 Scopus 的学术产出篇数、作品被引次数及无量纲学科加权引用影响力，非各国官方或全球全部科研成果；国家与地区名称和代码按源站返回。年度被引数归年口径尚未核实，不应直接视为当年全部新增引文。来源更新与覆盖年份按响应为准，自引设置只对适用指标生效；跨国合著与索引覆盖会影响比较。'}
