"""OCHA HAPI refugees, returnees, conflict events and baseline population."""
import release_runtime
import re, datetime
from ocha_hapi_adapter import _get
THEMES = {'refugees': 'affected-people/refugees-persons-of-concern', 'returnees': 'affected-people/returnees', 'conflict': 'coordination-context/conflict-events', 'baseline-population': 'geography-infrastructure/baseline-population'}

def data(theme, country, role=None, start=None, end=None, limit=20, offset=0):
    if theme not in THEMES:
        raise ValueError('未知主题')
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('国家须为三位大写代码')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('每页须为 1 至 100')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 0 <= offset <= 100000):
        raise ValueError('起始位置超出范围')
    params = {'limit': limit, 'offset': offset, 'output_format': 'json'}
    if theme in ('refugees', 'returnees'):
        if role not in ('origin', 'asylum'):
            raise ValueError('难民及返乡者必须明确 origin 来源国或 asylum 庇护国')
        params[role + '_location_code'] = country
    else:
        if role is not None:
            raise ValueError('此主题不适用来源国/庇护国角色')
        params['location_code'] = country
    for label, value in (('start_date', start), ('end_date', end)):
        if value is not None:
            if not isinstance(value, str) or not re.fullmatch('\\d{4}-\\d{2}-\\d{2}', value):
                raise ValueError('日期须为 YYYY-MM-DD')
            datetime.date.fromisoformat(value)
            params[label] = value
    if start and end and (start > end):
        raise ValueError('开始日期不得晚于结束日期')
    x = _get(THEMES[theme], params)
    x['theme'] = theme
    x['country_role'] = role
    x['note'] = '原样保留来源资源 ID、报告期、单位与标记。难民与返乡者区分来源国及庇护国；人口基准与流动人数不同；冲突事件数据不代表全部实际事件。空结果不是零。当前接口历史数值可能修订，报告日期不证明过去可得；须查看来源机构、覆盖与许可证。'
    return x
