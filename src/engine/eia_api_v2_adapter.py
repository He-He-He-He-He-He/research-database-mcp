"""EIA API v2 hierarchical discovery, facets, and filtered data."""
import release_runtime
import json
import re
import subprocess
import requests
BASE = 'https://api.eia.gov/v2/'
SERVICE = 'research-toolkit-eia'

def _key():
    from imap_otp_mcp.server import config
    account, _, _ = config()
    r = release_runtime.run(['/usr/bin/security', 'find-generic-password', '-s', SERVICE, '-a', account, '-w'], capture_output=True, text=True, timeout=15)
    if r.returncode or not r.stdout.strip():
        raise RuntimeError('无法读取本机 EIA 密钥')
    return r.stdout.strip()

def _route(value):
    if not isinstance(value, str) or len(value) > 250:
        raise ValueError('invalid route')
    value = value.strip('/')
    if value and any((not re.fullmatch('[A-Za-z0-9_-]+', x) for x in value.split('/'))):
        raise ValueError('invalid route')
    return value

def _fetch(path, params=None):
    key = _key()
    query = dict(params or {})
    query['api_key'] = key
    try:
        with requests.get(BASE + path, params=query, timeout=(10, 35), stream=True, allow_redirects=False) as r:
            if r.status_code != 200:
                raise RuntimeError('EIA API returned HTTP ' + str(r.status_code))
            b = bytearray()
            for chunk in r.iter_content(65536):
                b.extend(chunk)
                if len(b) > 16000000:
                    raise ValueError('EIA response exceeds 16 MB')
    except requests.RequestException:
        raise RuntimeError('EIA API network request failed') from None
    try:
        j = json.loads(b.decode('utf-8-sig'))
    except (UnicodeDecodeError, ValueError):
        raise RuntimeError('EIA returned invalid JSON') from None
    if not isinstance(j, dict) or not isinstance(j.get('response'), dict):
        raise RuntimeError('EIA returned unexpected response')

    def redact(x):
        if isinstance(x, str):
            return x.replace(key, '[redacted]')
        if isinstance(x, list):
            return [redact(v) for v in x]
        if isinstance(x, dict):
            return {k: redact(v) for k, v in x.items() if k.lower() not in ('api_key', 'apikey')}
        return x
    return {'source': 'US EIA API v2', 'api_version': j.get('apiVersion'), 'response': redact(j['response'])}

def browse(route=''):
    route = _route(route)
    return _fetch(route + '/' if route else '')

def discover(keyword, route='', max_requests=5, limit=30):
    route = _route(route)
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100:
        raise ValueError('invalid keyword')
    if type(max_requests) is not int or not 1 <= max_requests <= 25 or type(limit) is not int or (not 1 <= limit <= 100):
        raise ValueError('invalid search bounds')
    queue = [route]
    visited = set()
    matches = []
    failures = []
    skipped = []
    requests_count = 0
    q = keyword.strip().casefold()
    while queue and requests_count < max_requests:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        requests_count += 1
        try:
            response = browse(current)['response']
        except (RuntimeError, ValueError) as exc:
            failures.append({'route': current, 'error': str(exc)})
            continue
        own = {'route': current, 'name': response.get('name'), 'description': response.get('description')}
        if q in json.dumps(own, ensure_ascii=False).casefold():
            matches.append(own)
        children = response.get('routes', [])
        if not isinstance(children, list):
            raise RuntimeError('EIA returned invalid route list')
        for child in children:
            if not isinstance(child, dict) or not isinstance(child.get('id'), str):
                skipped.append({'parent': current, 'reason': 'missing child id'})
                continue
            part = child['id']
            if not re.fullmatch('[A-Za-z0-9_-]+', part):
                skipped.append({'parent': current, 'reason': 'unsupported child id'})
                continue
            child_route = (current + '/' if current else '') + part
            if child_route not in visited and child_route not in queue:
                queue.append(child_route)
    return {'source': 'US EIA API v2', 'keyword': keyword.strip(), 'root': route, 'requests': requests_count, 'matches': matches[:limit], 'matching_visited': len(matches), 'matches_truncated': len(matches) > limit, 'pending_routes': queue, 'failed_routes': failures, 'skipped_routes': skipped, 'complete': not queue and (not failures) and (not skipped), 'note': '仅在已访问的目录名称和说明中匹配；请求次数有限，未访问、跳过或失败的目录不代表无匹配。'}

def facet(route, facet_id):
    route = _route(route)
    facet_id = _route(facet_id)
    if not route or not facet_id or '/' in facet_id:
        raise ValueError('invalid route or facet')
    return _fetch(route + '/facet/' + facet_id + '/')

def data(route, fields, frequency, start='', end='', facets=None, offset=0, length=100):
    route = _route(route)
    if not route or not isinstance(fields, list) or (not 1 <= len(fields) <= 20) or any((not isinstance(x, str) or not re.fullmatch('[A-Za-z0-9_-]+', x) for x in fields)):
        raise ValueError('invalid route or data fields')
    if not isinstance(frequency, str) or not re.fullmatch('[A-Za-z0-9_-]{1,30}', frequency):
        raise ValueError('invalid frequency')
    for x in (start, end):
        if not isinstance(x, str) or (x and (not re.fullmatch('[0-9A-Za-z-]{1,20}', x))):
            raise ValueError('invalid period')
    if type(offset) is not int or offset < 0 or type(length) is not int or (not 1 <= length <= 5000):
        raise ValueError('invalid pagination')
    if facets is None:
        facets = {}
    if not isinstance(facets, dict) or len(facets) > 20:
        raise ValueError('invalid facets')
    p = {'data[]': fields, 'frequency': frequency, 'offset': offset, 'length': length}
    for name, values in facets.items():
        if not isinstance(name, str) or not re.fullmatch('[A-Za-z0-9_-]+', name) or (not isinstance(values, list)) or (not 1 <= len(values) <= 30) or any((not isinstance(v, str) or not re.fullmatch('[A-Za-z0-9_.-]{1,80}', v) for v in values)):
            raise ValueError('invalid facet')
        p['facets[' + name + '][]'] = values
    if start:
        p['start'] = start
    if end:
        p['end'] = end
    result = _fetch(route + '/data/', p)
    result.update({'route': route, 'filters': {'fields': fields, 'frequency': frequency, 'start': start, 'end': end, 'facets': facets, 'offset': offset, 'length': length}, 'note': '保留源站原值、单位与数据说明；分页总数和结果可随源站更新而变化。'})
    return result
