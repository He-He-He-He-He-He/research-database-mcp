"""UNDP HDRO DataPrism: metadata discovery and bounded data queries."""
import release_runtime
import json
import re
import subprocess
import requests
BASE = 'https://prism.hdrdata.org/api/'
SERVICE = 'research-toolkit-undp-dataprism'
KINDS = {'datasets', 'classifications', 'countries', 'regions', 'indicators', 'scenarios', 'timeperiods'}

def _key():
    from imap_otp_mcp.server import config
    account, _, _ = config()
    result = release_runtime.run(['/usr/bin/security', 'find-generic-password', '-s', SERVICE, '-a', account, '-w'], capture_output=True, text=True, timeout=15)
    if result.returncode or not result.stdout.strip():
        raise RuntimeError('无法读取本机钥匙串中的 DataPrism 密钥')
    return result.stdout.strip()

def _fetch(path, params=None):
    with requests.get(BASE + path, params=params, headers={'X-API-Key': _key()}, timeout=(10, 40), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.status_code != 200:
            raise RuntimeError('DataPrism returned unexpected HTTP status')
        buf = bytearray()
        for chunk in r.iter_content(65536):
            buf.extend(chunk)
            if len(buf) > 32000000:
                raise ValueError('DataPrism response exceeds 32 MB; narrow query')
    try:
        data = json.loads(buf.decode('utf-8-sig'))
    except (UnicodeDecodeError, ValueError):
        raise RuntimeError('DataPrism returned invalid JSON') from None
    if not isinstance(data, list):
        raise RuntimeError('DataPrism returned unexpected response structure')
    return data

def metadata(kind, keyword='', offset=0, limit=30, *, levels='', parent='', codes='', classifications=''):
    if kind not in KINDS:
        raise ValueError('unknown metadata kind')
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('invalid keyword')
    if type(offset) is not int or offset < 0 or type(limit) is not int or (not 1 <= limit <= 100):
        raise ValueError('invalid pagination')
    if levels and kind not in ('countries', 'regions') or (parent and kind != 'regions') or ((codes or classifications) and kind != 'indicators'):
        raise ValueError('filters do not apply to metadata kind')
    params = {}
    if levels:
        params['geographicLevels' if kind == 'countries' else 'hierarchyLevel'] = _list(levels, 'levels', '[A-Za-z0-9_.-]+')
        if kind == 'regions' and ',' in params['hierarchyLevel']:
            raise ValueError('regions accepts one hierarchy level')
    if parent:
        params['parentGeoId'] = _list(parent, 'parent', '[A-Za-z0-9_.-]+')
    if parent and ',' in params['parentGeoId']:
        raise ValueError('regions accepts one parent')
    if codes:
        params['codes'] = _list(codes, 'codes', '[A-Za-z0-9_.-]+')
    if classifications:
        params['classificationCodes'] = _list(classifications, 'classifications', '[A-Za-z0-9_.-]+')
    values = _fetch('metadata/' + kind, params or None)
    if keyword.strip():
        q = keyword.strip().casefold()
        values = [x for x in values if isinstance(x, dict) and q in json.dumps(x, ensure_ascii=False).casefold()]
    return {'source': 'UNDP HDRO DataPrism', 'kind': kind, 'keyword': keyword, 'source_filters': params, 'offset': offset, 'limit': limit, 'total_matches': len(values), 'items': values[offset:offset + limit], 'note': '指定维度由源站过滤，关键词匹配和分页在本机对返回的元数据执行；结果随源站更新。'}

def _list(value, name, pattern):
    if not isinstance(value, str) or len(value) > 1000:
        raise ValueError('invalid ' + name)
    items = [x.strip() for x in value.split(',')]
    if not items or len(items) > 30 or any((not re.fullmatch(pattern, x) for x in items)):
        raise ValueError('invalid ' + name)
    return ','.join(items)

def data(dataset, indicators, geos, periods, scenarios='', classifications=''):
    params = {'datasetIds': _list(dataset, 'dataset', '\\d+'), 'indicatorIds': _list(indicators, 'indicators', '\\d+'), 'geoIds': _list(geos, 'geos', '[A-Za-z0-9_.-]+'), 'timePeriodIds': _list(periods, 'periods', '\\d+')}
    if scenarios:
        params['scenarioIds'] = _list(scenarios, 'scenarios', '\\d+')
    if classifications:
        params['classificationCodes'] = _list(classifications, 'classifications', '[A-Za-z0-9_.-]+')
    rows = _fetch('data', params)
    return {'source': 'UNDP HDRO DataPrism', 'request': params, 'count': len(rows), 'rows': rows, 'note': '原始值与来源字段原样保留；请核验数据集版本、计量单位、情景和估计属性；这不是按历史时点还原的快照。'}
