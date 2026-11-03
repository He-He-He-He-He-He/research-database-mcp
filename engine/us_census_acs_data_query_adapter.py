"""ACS arbitrary-variable query; requires a Census API key for data."""
import release_runtime
import os, re
from urllib.parse import urlencode
from us_census_acs_adapter import _base, _get, DISCLAIMER

def query(year, series, variables, geography, within=''):
    if type(year) is not int:
        raise ValueError('year must be an integer')
    base = _base(year, series)
    if not isinstance(variables, str) or not re.fullmatch('[A-Za-z][A-Za-z0-9_]*(?:,[A-Za-z][A-Za-z0-9_]*){0,49}', variables):
        raise ValueError('provide 1–50 comma-separated ACS variables')
    names = variables.split(',')
    if len(set(names)) != len(names):
        raise ValueError('duplicate variable')
    geo = '[A-Za-z][A-Za-z0-9 ]{0,59}:(?:[0-9]+|\\*)'
    if not isinstance(geography, str) or not re.fullmatch(geo, geography):
        raise ValueError('invalid for geography, e.g. state:06 or county:*')
    if not isinstance(within, str) or (within and (not re.fullmatch(geo + '(?: ' + geo + ')*', within))):
        raise ValueError('invalid in geography, e.g. state:06')
    key = release_runtime.environment.get('US_CENSUS_API_KEY', '')
    if not key:
        raise ValueError('Census data service requires US_CENSUS_API_KEY; obtain and activate an official key')
    params = {'get': variables, 'for': geography}
    if within:
        params['in'] = within
    try:
        data = _get(base, {**params, 'key': key})
    except Exception as e:
        raise RuntimeError('Census data request failed or returned non-JSON; verify variables, geography, key and service status') from None
    if not isinstance(data, list) or not data or (not isinstance(data[0], list)) or any((not isinstance(r, list) or len(r) != len(data[0]) for r in data)):
        raise RuntimeError('unexpected Census table response')
    if any((v not in data[0] for v in names)):
        raise RuntimeError('response is missing requested variables')
    return {'source': base, 'request_url_without_key': base + '?' + urlencode(params), 'year': year, 'series': series, 'requested_variables': names, 'for': geography, 'in': within or None, 'header': data[0], 'rows': data[1:], 'disclaimer': DISCLAIMER, 'note': '保留 Census API 原始字符串；负数占位符和空值须按变量文档识别，不当作零。ACS 为抽样估计，E/M 分别对应估计值和误差，acs1 与 acs5 的覆盖及时间范围不同。'}
