"""Scopus author name/affiliation search using official user-selected fields."""
import release_runtime
from elsevier_scopus_official_adapter import author_search as upstream

def search(surname, given='', affiliation='', start=0, count=5):
    for v in (surname, given, affiliation):
        if not isinstance(v, str) or len(v) > 100 or any((c in v for c in ['"', '\\', '\n', '\r'])):
            raise ValueError('invalid name or affiliation')
    if not surname.strip():
        raise ValueError('surname is required')
    query = 'AUTHLAST("' + surname.strip() + '")'
    if given.strip():
        query += ' AND AUTHFIRST("' + given.strip() + '")'
    if affiliation.strip():
        query += ' AND AFFIL("' + affiliation.strip() + '")'
    x = upstream(query, start, count)
    x['structured_filters'] = {'surname': surname.strip(), 'given': given.strip() or None, 'affiliation': affiliation.strip() or None}
    x['note'] += ' 检索结果可能包含姓名变体、同名及近似姓名，必须由用户根据机构、领域和作者 ID 消歧后再选择详情或 SciVal 指标。'
    return x
