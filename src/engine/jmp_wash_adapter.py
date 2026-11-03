"""WHO/UNICEF JMP 饮水、卫生设施和个人卫生官方公开 API。"""
import release_runtime
import re
import requests
BASE = 'https://api.washdata.org/v1/'

def country_estimates(country, setting='household', service_type=None, service_level=None, residence=None, start=2000, end=None, limit=100, offset=0):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country 须为 ISO 三字母代码')
    if setting not in {'household', 'school', 'healthcare'}:
        raise ValueError('setting 仅支持 household、school、healthcare')
    if service_type is not None and service_type not in {'Drinking water', 'Sanitation', 'Hygiene'}:
        raise ValueError('service_type 无效')
    if service_level is not None and (not isinstance(service_level, str) or len(service_level) > 100):
        raise ValueError('service_level 无效')
    if residence is not None and (setting != 'household' or residence not in {'total', 'urban', 'rural'}):
        raise ValueError('residence 仅 household 支持 total、urban、rural')
    for y in (start, end):
        if y is not None and (isinstance(y, bool) or not isinstance(y, int) or (not 1900 <= y <= 2100)):
            raise ValueError('年份须为 1900 至 2100 的整数')
    if start and end and (start > end):
        raise ValueError('开始年份不能晚于结束年份')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 1000):
        raise ValueError('limit 须为 1 至 1000')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise ValueError('offset 须为非负整数')
    p = {'country[]': country, 'limit': limit, 'offset': offset}
    if start is not None:
        p['year_from'] = start
    if end is not None:
        p['year_to'] = end
    if service_type:
        p['service_type[]'] = service_type
    if service_level:
        p['service_level[]'] = service_level
    if residence:
        p['residence[]'] = residence
    r = requests.get(BASE + setting + '/estimates/country', params=p, timeout=25)
    r.raise_for_status()
    d = r.json()
    if not isinstance(d.get('results'), list) or not isinstance(d.get('total_count'), int):
        raise RuntimeError('JMP 返回的响应结构异常')
    if any((row.get('country') != country for row in d['results'])):
        raise RuntimeError('JMP 返回了非预期国家')
    return {'source': 'WHO/UNICEF JMP 官方 WASH API', 'setting': setting, 'query': d.get('query'), 'result_count': d.get('result_count'), 'total_count': d['total_count'], 'limit': limit, 'offset': offset, 'items': d['results'], 'scope': '覆盖比例是估计值、单位为百分比；对应家庭人口或学校/医疗设施。服务等级互不等同；空结果可能是无估计而非零。', 'documentation': 'https://washdata.org/data/api'}

def service_levels(setting='household'):
    if setting not in {'household', 'school', 'healthcare'}:
        raise ValueError('setting 无效')
    r = requests.get(BASE + setting + '/service-levels', timeout=25)
    r.raise_for_status()
    d = r.json()
    if not isinstance(d.get('results'), list):
        raise RuntimeError('JMP 定义响应异常')
    return {'source': 'WHO/UNICEF JMP 官方 WASH API', 'setting': setting, 'items': d['results'], 'documentation': 'https://washdata.org/data/api'}
