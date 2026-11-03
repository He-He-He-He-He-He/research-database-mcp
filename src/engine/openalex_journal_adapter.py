"""OpenAlex journal metadata and source-level metrics; independent of CAS rankings."""
import release_runtime
import re
import requests
from urllib.parse import urlencode
BASE = 'https://api.openalex.org/sources'
HEADERS = {'Accept': 'application/json', 'User-Agent': 'PersonalResearchToolkit/1.0'}
NOTE = 'OpenAlex 来源级指标及其覆盖范围与中国科学院期刊分区、JCR 期刊影响因子不同，不可相互替代。无 API key 请求共享所在 IP 的匿名额度；覆盖与结果会变化。'

def _get(url, params, session):
    r = (session or requests).get(url, params=params, headers=HEADERS, timeout=25)
    r.raise_for_status()
    d = r.json()
    if not isinstance(d, dict):
        raise ValueError('OpenAlex 响应格式异常')
    return d

def _validate_page(d, page, size):
    meta = d.get('meta') if isinstance(d, dict) else None
    results = d.get('results') if isinstance(d, dict) else None
    if not isinstance(meta, dict) or type(meta.get('count')) is not int or meta['count'] < 0 or (type(meta.get('page')) is not int) or (meta['page'] != page) or (type(meta.get('per_page')) is not int) or (meta['per_page'] != size) or (not isinstance(results, list)) or (len(results) > min(size, max(0, meta['count'] - (page - 1) * size))) or any((not isinstance(x, dict) or x.get('type') != 'journal' for x in results)):
        raise ValueError('OpenAlex 期刊页码、数量或类型异常')

def search(name, size=5, page=1, session=None):
    if not isinstance(name, str) or not name.strip() or len(name) > 150:
        raise ValueError('刊名无效')
    if type(size) is not int or not 1 <= size <= 10 or type(page) is not int or (not 1 <= page <= 100):
        raise ValueError('分页参数无效')
    p = {'search': name.strip(), 'filter': 'type:journal', 'per-page': size, 'page': page}
    d = _get(BASE, p, session)
    _validate_page(d, page, size)
    return {'source': 'OpenAlex sources (independent journal metadata)', 'source_url': BASE + '?' + urlencode(p), 'documentation': 'https://developers.openalex.org/api-reference/sources', 'note': NOTE, 'data': d}

def detail(source_id, session=None):
    if not isinstance(source_id, str) or not re.fullmatch('S\\d+', source_id):
        raise ValueError('来源编号应为 S 加数字')
    d = _get(BASE + '/' + source_id, None, session)
    if d.get('id') != 'https://openalex.org/' + source_id or d.get('type') != 'journal':
        raise ValueError('来源编号不匹配或不是期刊')
    return {'source': 'OpenAlex sources (independent journal metadata)', 'source_url': BASE + '/' + source_id, 'note': NOTE, 'data': d}
