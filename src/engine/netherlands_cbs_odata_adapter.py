"""Statistics Netherlands CBS OData 4 dataset catalogue and observations.

Values are coded: consult Properties, Dimensions and MeasureCodes and each
corresponding dimension code list for labels, units, revisions and scope.
"""
import release_runtime
import re
import requests
BASE = 'https://datasets.cbs.nl/odata/v1/CBS/'

def _id(x):
    if not isinstance(x, str) or not re.fullmatch('[A-Za-z0-9_]{1,80}', x):
        raise ValueError('invalid CBS identifier')
    return x

def _pagination(top, skip):
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (top, skip))) or not 1 <= top <= 1000 or skip < 0:
        raise ValueError('top must be 1..1000 and skip nonnegative')

def _get(path, params=None):
    r = requests.get(BASE + path, params=params, timeout=35)
    r.raise_for_status()
    return r.json()

def datasets(query='', top=20, skip=0, status=''):
    _pagination(top, skip)
    params = {'$top': top, '$skip': skip}
    filters = []
    if query:
        if not isinstance(query, str) or len(query) > 100:
            raise ValueError('invalid query')
        filters.append("contains(Title,'" + query.replace("'", "''") + "')")
    if status:
        if not isinstance(status, str) or len(status) > 50 or any((ord(c) < 32 for c in status)):
            raise ValueError('invalid status')
        filters.append("Status eq '" + status.replace("'", "''") + "'")
    if filters:
        params['$filter'] = ' and '.join(filters)
    result=_get('Datasets', params)
    if not isinstance(result,dict) or not isinstance(result.get('value'),list):raise ValueError('CBS catalog schema changed')
    result['query_info']={'keyword':query,'actual_filter':params.get('$filter'),'top':top,'skip':skip,'catalog':'CBS','search_field':'Title','search_method':'contains; no $search fallback','language_note':'该目录以荷语标题为主；英文关键词可能零命中，不代表没有相关数据。'}
    if not result['value']:
        hints={'population':'Bevolking','employment':'Arbeid','prices':'Prijzen','inflation':'Prijzen','人口':'Bevolking','就业':'Arbeid','价格':'Prijzen'}
        term=hints.get(query.casefold())
        result['empty_result']=True;result['empty_reason']='no_match'
        if term:result['suggested_queries']=[{'query':term,'reason':'建议单独尝试荷语标题词；未自动修改本次过滤条件。'}]
    return result

def properties(dataset):
    return _get(_id(dataset) + '/Properties')

def dimensions(dataset):
    return _get(_id(dataset) + '/Dimensions')

def codes(dataset, dimension='Measure', top=100, skip=0):
    _pagination(top, skip)
    return _get(_id(dataset) + '/' + _id(dimension) + 'Codes', {'$top': top, '$skip': skip})

def observations(dataset, filters=None, top=100, skip=0):
    """Fetch a page; dimension equality filters are combined with AND."""
    _pagination(top, skip)
    params = {'$top': top, '$skip': skip}
    if filters:
        if not isinstance(filters, dict):
            raise ValueError('filters must be a mapping')
        terms = []
        for key, value in filters.items():
            _id(key)
            if not isinstance(value, str) or len(value) > 100:
                raise ValueError('invalid filter value')
            terms.append(key + " eq '" + value.replace("'", "''") + "'")
        params['$filter'] = ' and '.join(terms)
    return _get(_id(dataset) + '/Observations', params)
