"""UNHCR country-code discovery and asylum-country-centred statistics."""
import release_runtime
import re, requests
from unhcr_population_adapter import _countries, _resolve
BASE = 'https://api.unhcr.org/population/v1/'
DOC = 'https://api.unhcr.org/docs/refugee-statistics.html'
KINDS = {'population': 'population/', 'demographics': 'demographics/', 'applications': 'asylum-applications/', 'decisions': 'asylum-decisions/'}

def countries(keyword='', limit=30, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词无效')
    if type(limit) is not int or not 1 <= limit <= 100 or type(offset) is not int or (not 0 <= offset <= 10000):
        raise ValueError('分页无效')
    q = keyword.strip().casefold()
    rows = [x for x in _countries() if q in ' '.join((str(x.get(k, '')) for k in ('code', 'iso', 'iso2', 'name', 'nameFormal', 'nationality'))).casefold()]
    return {'source_url': BASE + 'countries/', 'keyword': keyword, 'matched': len(rows), 'offset': offset, 'items': rows[offset:offset + limit], 'note': '目录包含国家和地区，UNHCR 自有代码与 ISO 不一定相同，如埃及 ARE 对应 ISO EGY；目录不代表各年有观测。'}

def by_asylum(kind, year, asylum, code_system='iso3', mode='origins', page=1, limit=20):
    if kind not in KINDS or code_system not in ('unhcr', 'iso3') or mode not in ('origins', 'aggregate'):
        raise ValueError('类别、代码体系或汇总方式无效')
    if type(year) is not int or not 1950 <= year <= 2100:
        raise ValueError('年份无效')
    if not isinstance(asylum, str) or not re.fullmatch('[A-Z]{3}', asylum):
        raise ValueError('国家代码须为 3 个大写字母')
    if type(page) is not int or page < 1 or type(limit) is not int or (not 1 <= limit <= 100):
        raise ValueError('分页无效')
    actual = _resolve(asylum, code_system)
    p = {'year': year, 'coa': actual, 'page': page, 'limit': limit}
    if mode == 'origins':
        p['coo_all'] = 'true'
    r = requests.get(BASE + KINDS[kind], params=p, timeout=35)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, dict) or not isinstance(j.get('items'), list) or j.get('page') != page:
        raise RuntimeError('UNHCR 返回结构或页码异常')
    if any((row.get('coa') != actual or row.get('year') != year for row in j['items'])):
        raise RuntimeError('返回的庇护国或年份不匹配')
    return {'source_url': r.url, 'documentation': DOC, 'kind': kind, 'input_country': asylum, 'input_code_system': code_system, 'unhcr_asylum_code': actual, 'mode': mode, 'result': j, 'note': 'origins 按来源国分列，aggregate 为来源国维度汇总，二者不可相加。population 是人数存量，applications/decisions 是申请或决定记录，demographics 为人口结构，口径不同。原值、零和缺失标记保留；地区覆盖和历史值可修订，页次随更新变化。'}
