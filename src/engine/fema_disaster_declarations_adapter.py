"""FEMA OpenFEMA disaster declaration area records v2."""
import release_runtime
import re
import requests
BASE = 'https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries'

def declarations(state=None, fiscal_year=None, disaster_number=None, declaration_type=None, limit=20, offset=0):
    if not 1 <= int(limit) <= 1000 or int(offset) < 0:
        raise ValueError('limit 须为 1–1000，offset 须非负')
    filters = []
    if state is not None:
        state = str(state).upper()
        if not re.fullmatch('[A-Z]{2}', state):
            raise ValueError('state 必须是两位字母代码')
        filters.append("state eq '" + state + "'")
    if fiscal_year is not None:
        if not 1950 <= int(fiscal_year) <= 2100:
            raise ValueError('财政年度无效')
        filters.append('fyDeclared eq ' + str(int(fiscal_year)))
    if disaster_number is not None:
        if int(disaster_number) < 1:
            raise ValueError('灾害编号无效')
        filters.append('disasterNumber eq ' + str(int(disaster_number)))
    if declaration_type is not None:
        if declaration_type not in ('DR', 'EM', 'FM'):
            raise ValueError('声明类型限 DR、EM、FM')
        filters.append("declarationType eq '" + declaration_type + "'")
    params = {'$top': int(limit), '$skip': int(offset)}
    if filters:
        params['$filter'] = ' and '.join(filters)
    r = requests.get(BASE, params=params, timeout=35)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j.get('DisasterDeclarationsSummaries'), list):
        raise RuntimeError('未返回灾害声明记录')
    return {'url': r.url, 'metadata': j.get('metadata'), 'records': j['DisasterDeclarationsSummaries'], 'note': '每条为声明指定区域记录，同一灾害可出现多行；不是所有灾害事件。'}
