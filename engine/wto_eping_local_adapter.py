"""WTO ePing public API: members and SPS/TBT notification metadata."""
import release_runtime
import json, re, subprocess
from datetime import date
import requests
BASE = 'https://api.wto.org/eping/'

def _get(path, params):
    p = release_runtime.run(['security', 'find-generic-password', '-s', 'research-toolkit-wto-standard', '-a', 'zju-research-toolkit', '-w'], capture_output=True, text=True, timeout=15)
    if p.returncode or not p.stdout.strip():
        raise RuntimeError('WTO Keychain credential unavailable')
    try:
        with requests.get(BASE + path, params=params, headers={'Ocp-Apim-Subscription-Key': p.stdout.strip()}, timeout=30, stream=True, allow_redirects=False) as r:
            if r.is_redirect:
                raise RuntimeError('Unexpected WTO redirect')
            if not r.ok:
                raise RuntimeError('WTO ePing returned HTTP ' + str(r.status_code))
            parts = []
            n = 0
            for b in r.iter_content(65536):
                n += len(b)
                if n > 8 * 1024 * 1024:
                    raise RuntimeError('Response exceeds 8 MiB')
                parts.append(b)
        data = json.loads(b''.join(parts))
    except requests.RequestException as e:
        raise RuntimeError('WTO ePing network request failed: ' + type(e).__name__) from None
    if not isinstance(data, dict) or not isinstance(data.get('items'), list):
        raise RuntimeError('Unexpected WTO ePing response')
    return data

def members(language=1):
    if type(language) is not int or language not in (1, 2, 3):
        raise ValueError('language must be 1, 2 or 3')
    data = _get('members', {'language': language})
    return {'source': 'WTO ePing', 'source_info': 'https://apiportal.wto.org/api-details#api=eping', 'language': language, 'response': data, 'note': '成员代码与名称，按上游提供，不代表每个通知的法律地位。'}

def search(query='', language=1, domain=None, since=None, until=None, page=1, page_size=20):
    if not isinstance(query, str) or len(query) > 200:
        raise ValueError('query too long')
    if type(language) is not int or language not in (1, 2, 3) or (domain is not None and (type(domain) is not int or domain not in (1, 2))):
        raise ValueError('invalid language or domain')
    if isinstance(page, bool) or not isinstance(page, int) or page < 1 or isinstance(page_size, bool) or (not isinstance(page_size, int)) or (not 1 <= page_size <= 100):
        raise ValueError('invalid page')
    dates = []
    for s in (since, until):
        dates.append(date.fromisoformat(s) if s else None)
    if all(dates) and dates[0] > dates[1]:
        raise ValueError('invalid date range')
    params = {'language': language, 'page': page, 'pageSize': page_size}
    if query:
        params['freeText'] = query
    if domain:
        params['domainIds'] = domain
    if since:
        params['distributionDateFrom'] = dates[0].isoformat()
    if until:
        params['distributionDateTo'] = dates[1].isoformat()
    data = _get('notifications/search', params)
    return {'source': 'WTO ePing', 'source_info': 'https://apiportal.wto.org/api-details#api=eping', 'selection': params, 'response': data, 'note': 'SPS/TBT 通报检索，并非法规生效或最终措施的证明。保留原始日期、编号与总数，页码从1开始；应查原通报及官方后续更新。'}
