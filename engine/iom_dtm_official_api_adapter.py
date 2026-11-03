"""IOM DTM V3 official Baseline API, using the local macOS Keychain."""
import release_runtime
import datetime
import re
import subprocess
import requests
BASE = 'https://dtmapi.iom.int/v3/displacement/'
SERVICE = 'research-toolkit.iom-dtm'

def _key():
    result = release_runtime.run(['/usr/bin/security', 'find-generic-password', '-s', SERVICE, '-w'], capture_output=True, timeout=30)
    if result.returncode:
        raise RuntimeError('无法读取 IOM 钥匙串项目；请检查项目和 macOS 访问授权')
    value = result.stdout.decode('utf-8').strip()
    if not value:
        raise RuntimeError('IOM 订阅密钥为空')
    return value

def _get(path, params=None):
    with requests.get(BASE + path, params=params, headers={'Ocp-Apim-Subscription-Key': _key(), 'User-Agent': 'ResearchDatabaseToolkit/1.0'}, timeout=45, stream=True) as response:
        response.raise_for_status()
        chunks = []
        size = 0
        for chunk in response.iter_content(65536):
            size += len(chunk)
            if size > 8 * 1024 * 1024:
                raise ValueError('响应超过 8 MiB，请缩短时间范围')
            chunks.append(chunk)
    import json
    return json.loads(b''.join(chunks))

def countries():
    payload = _get('country-list')
    if not isinstance(payload, dict) or payload.get('isSuccess') is not True or (not isinstance(payload.get('result'), list)):
        raise ValueError('IOM 国家列表响应异常')
    return {'source': BASE + 'country-list', 'data': payload, 'note': 'IOM DTM 基础数据覆盖的国家目录；不等同完整全球移民数据库。'}

def observations(level, country, start, end, admin1=None):
    if level not in ('admin0', 'admin1', 'admin2'):
        raise ValueError('未知行政层级')
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('国家代码须为大写三字母代码')
    try:
        begin = datetime.date.fromisoformat(start)
        finish = datetime.date.fromisoformat(end)
    except (ValueError, TypeError):
        raise ValueError('日期须为 YYYY-MM-DD') from None
    if begin > finish or (finish - begin).days > 366:
        raise ValueError('时间范围须有序且不超过 366 天')
    params = {'Admin0Pcode': country, 'FromReportingDate': start, 'ToReportingDate': end}
    if admin1:
        if not re.fullmatch('[A-Za-z0-9_-]{1,30}', admin1):
            raise ValueError('无效一级地区代码')
        params['Admin1Pcode'] = admin1
    if level == 'admin2' and (not admin1):
        raise ValueError('admin2 查询须指定一级地区代码')
    payload = _get(level, params)
    if not isinstance(payload, dict) or payload.get('isSuccess') is not True or (not isinstance(payload.get('result'), list)):
        raise ValueError('IOM 数据响应异常')
    return {'source': BASE + level, 'parameters': params, 'data': payload, 'note': 'IOM 各轮评估快照，不能跨日期、类别或行政层级直接相加；空结果不等于零。'}

def admin0(country, start, end):
    return observations('admin0', country, start, end)
