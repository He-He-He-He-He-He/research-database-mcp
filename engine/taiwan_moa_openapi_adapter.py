"""台湾地区农业资料开放平台公布的 Swagger API；匿名首屏。"""
import release_runtime
import json
import re
import requests
SPEC = 'https://data.moa.gov.tw/openapi.json'
BASE = 'https://data.moa.gov.tw/api/v1/'

def _get(url, params=None, max_bytes=8000000):
    with requests.get(url, params=params, timeout=30, allow_redirects=False, stream=True) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise RuntimeError('官网服务重定向')
        chunks = []
        n = 0
        for chunk in r.iter_content(65536):
            n += len(chunk)
            if n > max_bytes:
                raise RuntimeError('官网响应超过大小上限')
            chunks.append(chunk)
    try:
        return json.loads(b''.join(chunks))
    except ValueError as e:
        raise RuntimeError('官网响应非 JSON') from e

def catalog(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词须不超过100字')
    spec = _get(SPEC)
    paths = spec.get('paths') if isinstance(spec, dict) else None
    if not isinstance(paths, dict):
        raise RuntimeError('官方 API 文档结构异常')
    items = []
    for path, entry in paths.items():
        op = entry.get('get') if isinstance(entry, dict) else None
        if not isinstance(op, dict) or not re.fullmatch('/[A-Za-z0-9_]+/', path):
            continue
        summary = op.get('summary', '')
        tags = op.get('tags', [])
        if keyword and keyword.casefold() not in (path + ' ' + str(summary) + ' ' + str(tags)).casefold():
            continue
        items.append({'path': path, 'summary': summary, 'tags': tags, 'parameters': [{'name': x.get('name'), 'required': x.get('required', False)} for x in op.get('parameters', []) if isinstance(x, dict)]})
    return {'source': '台湾地区农业资料开放平台官方 Swagger', 'url': SPEC, 'items': items, 'count': len(items), 'note': '目录来自官网文档；接口和参数不代表均已验证，部分操作或第二页需要注册密钥。'}

def query(path, parameters=None):
    if not isinstance(path, str) or not re.fullmatch('/[A-Za-z0-9_]+/', path):
        raise ValueError('接口路径无效')
    matches = [x for x in catalog()['items'] if x['path'] == path]
    if not matches:
        raise ValueError('接口不在官网文档目录')
    params = {} if parameters is None else parameters
    if not isinstance(params, dict):
        raise ValueError('参数须为字典')
    names = {x['name'] for x in matches[0]['parameters']}
    if any((k not in names or not isinstance(v, (str, int)) or isinstance(v, bool) or (len(str(v)) > 100) for k, v in params.items())):
        raise ValueError('参数不属于官方文档或格式无效')
    if 'Page' in params and str(params['Page']) != '1':
        raise ValueError('匿名接口仅允许查询第一页')
    d = _get(BASE + path.strip('/') + '/', params=params)
    if not isinstance(d, dict) or d.get('RS') != 'OK' or (not isinstance(d.get('Data'), list)):
        raise RuntimeError('官网接口未成功返回数据：' + str(d.get('MSG', '未知错误') if isinstance(d, dict) else '响应异常')[:150])
    return {'source': '台湾地区农业资料开放平台', 'path': path, 'summary': matches[0]['summary'], 'parameters': params, 'items': d['Data'], 'next': d.get('Next'), 'count_on_page': len(d['Data']), 'note': '匿名访问只验证首屏；Next 不代表可匿名访问下一页，数据口径和时效请核官网，许可或农药登记状态可能变更，不能据历史记录判定当前有效性。'}
