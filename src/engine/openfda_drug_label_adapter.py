"""FDA openFDA drug labeling records; research reference only."""
import release_runtime
import requests
from urllib.parse import urlencode
BASE = 'https://api.fda.gov/drug/label.json'
HEADERS = {'Accept': 'application/json', 'User-Agent': 'PersonalResearchToolkit/1.0'}
DISCLAIMER = 'FDA 提醒：不得依赖 openFDA 作医疗决策；结果可能未经验证。请由专业人员结合最新正式药品说明书核实。'

def search(name, field='generic', limit=3, skip=0, session=None):
    if not isinstance(name, str) or not name.strip() or len(name) > 100 or any((c in name for c in '\\"\r\n')):
        raise ValueError('药名无效')
    if field not in ('generic', 'brand', 'substance'):
        raise ValueError('药名字段无效')
    if type(limit) is not int or not 1 <= limit <= 10 or type(skip) is not int or (not 0 <= skip <= 25000):
        raise ValueError('分页参数无效')
    mapping = {'generic': 'generic_name', 'brand': 'brand_name', 'substance': 'substance_name'}
    params = {'search': 'openfda.' + mapping[field] + ':"' + name.strip() + '"', 'limit': limit, 'skip': skip}
    r = (session or requests).get(BASE, params=params, headers=HEADERS, timeout=25)
    if r.status_code == 404:
        d = r.json()
        e = d.get('error', {}) if isinstance(d, dict) else {}
        if e.get('code') == 'NOT_FOUND':
            return {'source': 'FDA openFDA Drug Labeling', 'source_url': BASE + '?' + urlencode(params), 'disclaimer': DISCLAIMER, 'query': params, 'data': d, 'items': []}
    r.raise_for_status()
    d = r.json()
    if not isinstance(d, dict) or not isinstance(d.get('results'), list) or (not isinstance(d.get('meta'), dict)):
        raise ValueError('openFDA 返回格式异常')
    return {'source': 'FDA openFDA Drug Labeling', 'source_url': BASE + '?' + urlencode(params), 'documentation': 'https://open.fda.gov/apis/drug/label/', 'disclaimer': DISCLAIMER, 'query': params, 'data': d}
