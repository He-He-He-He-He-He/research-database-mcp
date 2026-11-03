"""WTO Timeseries data API using a macOS Keychain subscription key."""
import release_runtime
import json, re, subprocess
import requests
URL = 'https://api.wto.org/timeseries/v1/data'
SERVICE = 'research-toolkit-wto-standard'
ACCOUNT = 'zju-research-toolkit'
MAX_BYTES = 8 * 1024 * 1024

def indicators(name, language=1, kind='indicators', classification=None):
    if not isinstance(name, str) or not name.strip() or len(name) > 100:
        raise ValueError('Name must contain 1–100 characters')
    if type(language) is not int or language not in (1, 2, 3):
        raise ValueError('Invalid language')
    if kind not in ('indicators', 'reporters', 'products'):
        raise ValueError('Invalid catalogue')
    if classification is not None and (kind != 'products' or not isinstance(classification, str) or (not re.fullmatch('[A-Za-z0-9_,.-]{1,100}', classification))):
        raise ValueError('Invalid classification')
    result = release_runtime.run(['security', 'find-generic-password', '-s', SERVICE, '-a', ACCOUNT, '-w'], capture_output=True, text=True, timeout=15)
    if result.returncode or not result.stdout.strip():
        raise RuntimeError('WTO Keychain credential unavailable')
    try:
        params = {'name': name, 'lang': language}
        if classification is not None:
            params['pc'] = classification
        with requests.get('https://api.wto.org/timeseries/v1/' + kind, params=params, headers={'Ocp-Apim-Subscription-Key': result.stdout.strip()}, timeout=30, stream=True, allow_redirects=False) as response:
            if response.is_redirect:
                raise RuntimeError('Unexpected WTO API redirect')
            if not response.ok:
                raise RuntimeError('WTO API returned HTTP ' + str(response.status_code))
            chunks = []
            size = 0
            for chunk in response.iter_content(65536):
                size += len(chunk)
                if size > MAX_BYTES:
                    raise RuntimeError('WTO response exceeds 8 MiB')
                chunks.append(chunk)
        raw = b''.join(chunks)
        try:
            body = raw.decode('utf-8')
            encoding = 'utf-8'
        except UnicodeDecodeError:
            body = raw.decode('cp1252')
            encoding = 'windows-1252 (fallback)'
        data = json.loads(body)
    except requests.RequestException as exc:
        raise RuntimeError('WTO API network request failed: ' + type(exc).__name__) from None
    if not isinstance(data, list):
        raise RuntimeError('Unexpected WTO catalogue response')
    return {'source': 'WTO Timeseries ' + kind + ' catalogue', 'source_info': 'https://apiportal.wto.org/api-details#api=version1&operation=get-' + kind, 'query': name, 'classification': classification, 'language': language, 'response_encoding': encoding, 'returned': len(data), 'items': data, 'note': '官方按名称筛选；代码和口径以来源为准，列表不代表所选国家均有数据。'}

def query(indicator, reporter, periods, partner='000', product='TO', offset=0, limit=100):
    for value in (indicator, reporter, periods) + tuple((v for v in (partner, product) if v is not None)):
        if not isinstance(value, str) or not re.fullmatch('[A-Za-z0-9_,.-]{1,120}', value):
            raise ValueError('Invalid WTO code or period selection')
    if ',' in indicator:
        raise ValueError('Only one indicator is supported')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 1000):
        raise ValueError('Invalid pagination')
    result = release_runtime.run(['security', 'find-generic-password', '-s', SERVICE, '-a', ACCOUNT, '-w'], capture_output=True, text=True, timeout=15)
    if result.returncode or not result.stdout.strip():
        raise RuntimeError('WTO Keychain credential unavailable')
    key = result.stdout.strip()
    params = {'i': indicator, 'r': reporter, 'ps': periods, 'fmt': 'json', 'off': offset, 'max': limit, 'meta': 'true'}
    if partner is not None:
        params['p'] = partner
    if product is not None:
        params['pc'] = product
    try:
        with requests.get(URL, params=params, headers={'Ocp-Apim-Subscription-Key': key}, timeout=30, stream=True, allow_redirects=False) as response:
            if response.is_redirect:
                raise RuntimeError('Unexpected WTO API redirect')
            if not response.ok:
                raise RuntimeError('WTO API returned HTTP ' + str(response.status_code))
            status = response.status_code
            chunks = []
            size = 0
            for chunk in response.iter_content(65536):
                size += len(chunk)
                if size > MAX_BYTES:
                    raise RuntimeError('WTO response exceeds 8 MiB; narrow selection')
                chunks.append(chunk)
        raw = b''.join(chunks)
        if status == 204:
            data = {'Dataset': []}
            encoding = 'none (HTTP 204)'
        else:
            try:
                body = raw.decode('utf-8')
                encoding = 'utf-8'
            except UnicodeDecodeError:
                body = raw.decode('cp1252')
                encoding = 'windows-1252 (fallback)'
            data = json.loads(body)
    except requests.RequestException as exc:
        raise RuntimeError('WTO API network request failed: ' + type(exc).__name__) from None
    if not isinstance(data, dict) or not isinstance(data.get('Dataset'), list):
        raise RuntimeError('Unexpected WTO API response')
    return {'source': 'WTO Timeseries API', 'source_info': 'https://apiportal.wto.org/', 'response_encoding': encoding, 'upstream_status': status, 'selection': {'indicator': indicator, 'reporter': reporter, 'partner': partner, 'product': product, 'periods': periods, 'offset': offset, 'limit': limit}, 'response': data, 'returned': len(data['Dataset']), 'note': '单指标查询；保留来源的产品、贸易伙伴、频率、单位和标记。HTTP 204 表示未返回数据，不代表数值为零。当前页不等于全部结果；核对上游汇总及分页。时间序列请求不得超过每秒1次；本模块不自动限流或重试。'}
