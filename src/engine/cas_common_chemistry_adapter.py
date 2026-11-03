"""CAS Common Chemistry registered public-subset API, non-commercial CC BY-NC 4.0."""
import release_runtime
import re, subprocess
import requests
from urllib.parse import urlencode
BASE = 'https://commonchemistry.cas.org/direct-api'
SERVICE = 'zju-research-toolkit'
ACCOUNT = 'research-toolkit-cas-common-chemistry'
NOTE = 'CAS Common Chemistry 仅覆盖 CAS REGISTRY 的公开子集，不是完整 SciFinder；数据依据 CC BY-NC 4.0 使用并须署名 CAS。商业用途及第三方服务适用性需核实；请勿将结果用作医疗决策。'

def _key():
    try:
        p = release_runtime.run(['/usr/bin/security', 'find-generic-password', '-s', SERVICE, '-a', ACCOUNT, '-w'], capture_output=True, text=True, timeout=10)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError('钥匙串访问超时；请检查本机授权') from exc
    if p.returncode or not p.stdout.strip():
        raise RuntimeError('无法读取 CAS Common Chemistry 钥匙串凭据')
    return p.stdout.strip()

def _request(path, params, session=None):
    key = _key()
    r = (session or requests).get(BASE + path, params=params, headers={'X-API-KEY': key, 'Accept': 'application/json'}, timeout=25)
    if r.status_code in (401, 403):
        raise RuntimeError('CAS 接口拒绝认证，请检查令牌或授权')
    r.raise_for_status()
    d = r.json()
    if not isinstance(d, dict):
        raise ValueError('CAS API 响应格式异常')
    return d

def search(query, size=5, offset=0, session=None):
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('检索词无效')
    if type(size) is not int or not 1 <= size <= 10 or type(offset) is not int or (not 0 <= offset <= 10000):
        raise ValueError('分页参数无效')
    p = {'q': query.strip(), 'size': size, 'offset': offset}
    d = _request('/search', p, session)
    if not isinstance(d.get('results'), list):
        raise ValueError('CAS 搜索响应缺少结果')
    items = []
    for x in d['results']:
        if not isinstance(x, dict) or not isinstance(x.get('rn'), str) or (not isinstance(x.get('name'), str)):
            raise ValueError('CAS 搜索记录异常')
        items.append({k: v for k, v in x.items() if k not in ('image', 'images')})
    return {'source': 'CAS Common Chemistry © American Chemical Society / CC BY-NC 4.0', 'source_url': BASE + '/search?' + urlencode(p), 'documentation': 'https://commonchemistry.cas.org/api-overview', 'query': query.strip(), 'total': d.get('count'), 'items': items, 'note': NOTE}

def detail(cas_rn, session=None):
    if not isinstance(cas_rn, str) or not re.fullmatch('\\d{2,7}-\\d{2}-\\d', cas_rn):
        raise ValueError('CAS RN 格式无效')
    p = {'cas_rn': cas_rn}
    d = _request('/detail', p, session)
    if d.get('rn') != cas_rn:
        raise ValueError('CAS 返回的登记号与请求不匹配')
    return {'source': 'CAS Common Chemistry © American Chemical Society / CC BY-NC 4.0', 'source_url': BASE + '/detail?' + urlencode(p), 'data': {k: v for k, v in d.items() if k not in ('image', 'images')}, 'note': NOTE}
