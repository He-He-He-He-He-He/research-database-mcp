"""IOM DTM Humanitarian Needs Assessment country coverage, authenticated locally."""
import release_runtime
import json
import subprocess
import re
import requests
BASE = 'https://dtmapi.iom.int/HNA/v1/'
SERVICE = 'research-toolkit.iom-hna'

def _get(path, params=None):
    result = release_runtime.run(['/usr/bin/security', 'find-generic-password', '-s', SERVICE, '-w'], capture_output=True, timeout=30)
    if result.returncode:
        raise RuntimeError('无法读取 IOM HNA 钥匙串项目；请检查钥匙串访问授权')
    key = result.stdout.decode('utf-8').strip()
    if not key:
        raise RuntimeError('IOM HNA 订阅密钥为空')
    with requests.get(BASE + path, params=params, headers={'Ocp-Apim-Subscription-Key': key, 'User-Agent': 'ResearchDatabaseToolkit/1.0'}, timeout=45, stream=True) as response:
        response.raise_for_status()
        parts, size = ([], 0)
        for chunk in response.iter_content(65536):
            size += len(chunk)
            if size > 8 * 1024 * 1024:
                raise ValueError('IOM HNA 响应超过 8 MiB')
            parts.append(chunk)
    payload = json.loads(b''.join(parts))
    if path == 'catalog' and isinstance(payload, list):
        return payload
    if not isinstance(payload, dict) or not (payload.get('isCompletedSuccessfully') is True or payload.get('isSuccess') is True):
        raise ValueError('IOM HNA 响应异常')
    return payload

def countries():
    result = _get('country-list')['result']
    if not isinstance(result, list):
        raise ValueError('IOM HNA 国家列表格式异常')
    return {'source': BASE + 'country-list', 'data': result, 'note': 'HNA 数据覆盖目录，并非所有国家；年份和人口组以返回内容为准。'}

def catalog(keyword=''):
    if len(keyword) > 100:
        raise ValueError('关键词过长')
    rows = _get('catalog')
    filtered = [item for item in rows if keyword.casefold() in ' '.join((str(v) for v in item.values())).casefold()]
    return {'source': BASE + 'catalog', 'total': len(rows), 'matching': len(filtered), 'data': filtered, 'note': '官方指标名称与问题描述；具体调查口径应结合原始问卷核对。'}

def admin2(country, year, population_group=None, page=1):
    if not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('国家代码须为大写三字母')
    if not 2000 <= year <= 2100 or not 1 <= page <= 10000:
        raise ValueError('无效年份或页码')
    if population_group and (len(population_group) > 80 or not re.fullmatch('[A-Za-z ,\\-]+', population_group)):
        raise ValueError('无效人口组')
    params = {'Admin0Pcode': country, 'Year': year, 'Page': page}
    if population_group:
        params['PopulationGroup'] = population_group
    payload = _get('admin2', params)
    if not isinstance(payload.get('result'), dict) or not isinstance(payload['result'].get('data'), list):
        raise ValueError('IOM HNA 地区数据格式异常')
    return {'source': BASE + 'admin2', 'parameters': params, 'data': payload['result'], 'note': '每页最多100条；核实指标定义、人口组及调查轮次，不应跨组或轮次直接相加。'}
