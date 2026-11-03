"""按名称、城市和国家检索 Scopus 官方机构档案。"""
import release_runtime
from elsevier_scopus_official_adapter import affiliation_search as upstream

def search(name, city='', country='', start=0, count=5):
    for label, value in [('name', name), ('city', city), ('country', country)]:
        if not isinstance(value, str) or len(value) > 200 or any((c in value for c in ('"', '\\', '\n', '\r'))) or any((ord(c) < 32 for c in value)):
            raise ValueError(label + ' 须为不含引号或控制字符的单行文本，最多 200 字')
    if not name.strip():
        raise ValueError('机构名称不能为空')
    query = 'AFFIL("' + name.strip() + '")'
    if city.strip():
        query += ' AND AFFILCITY("' + city.strip() + '")'
    if country.strip():
        query += ' AND AFFILCOUNTRY("' + country.strip() + '")'
    out = upstream(query, start, count)
    out['structured_filters'] = {'name': name.strip(), 'city': city.strip() or None, 'country': country.strip() or None}
    out['note'] += ' 结果可能包含名称变体和下属机构；必须核对每条名称、城市和 Scopus 机构 ID 后再使用，不能与 SciVal ID 混用。'
    return out
