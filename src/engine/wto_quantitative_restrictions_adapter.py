"""WTO official QR list: read-only trade restrictions notifications."""
import release_runtime
import json, re, subprocess
import requests
URL = 'https://api.wto.org/qrs/qrs'

def search(page=1, reporter=None, product=None, in_force=False, year=None, endpoint='qrs', name=None, identifier=None):
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise ValueError('Invalid page')
    if not isinstance(in_force, bool):
        raise ValueError('in_force must be boolean')
    if endpoint not in ('qrs', 'members', 'detail'):
        raise ValueError('Invalid endpoint')
    if endpoint != 'detail' and identifier is not None:
        raise ValueError('identifier is only applicable to detail')
    if endpoint in ('members', 'detail') and (reporter is not None or product is not None or in_force or (year is not None)):
        raise ValueError('QR filters apply only to the qrs endpoint')
    if endpoint == 'detail' and page != 1:
        raise ValueError('detail is not paginated')
    if endpoint == 'detail' and (isinstance(identifier, bool) or not isinstance(identifier, int) or identifier < 1):
        raise ValueError('Invalid QR identifier')
    if name is not None and (endpoint != 'members' or not isinstance(name, str) or len(name) > 100):
        raise ValueError('Invalid name')
    if reporter is not None and (not isinstance(reporter, str) or not re.fullmatch('[A-Za-z0-9]{1,15}', reporter)):
        raise ValueError('Invalid reporter code')
    if product is not None and (not isinstance(product, str) or not re.fullmatch('[0-9,]{1,120}', product)):
        raise ValueError('Invalid product code')
    if year is not None and (isinstance(year, bool) or not isinstance(year, int) or (not 1800 <= year <= 2100)):
        raise ValueError('Invalid year')
    p = release_runtime.run(['security', 'find-generic-password', '-s', 'research-toolkit-wto-standard', '-a', 'zju-research-toolkit', '-w'], capture_output=True, text=True, timeout=15)
    if p.returncode or not p.stdout.strip():
        raise RuntimeError('WTO Keychain credential unavailable')
    params = {} if endpoint == 'detail' else {'page': page}
    if name:
        params['name'] = name
    if reporter:
        params['reporter_member_code'] = reporter
    if product:
        params['product_codes'] = product
    if in_force:
        params['in_force_only'] = 'true'
    if year is not None:
        params['year_of_entry_into_force'] = year
    try:
        path = 'qrs/' + str(identifier) if endpoint == 'detail' else endpoint
        with requests.get('https://api.wto.org/qrs/' + path, params=params, headers={'Ocp-Apim-Subscription-Key': p.stdout.strip()}, timeout=35, stream=True, allow_redirects=False) as r:
            if r.is_redirect:
                raise RuntimeError('Unexpected WTO redirect')
            if not r.ok:
                raise RuntimeError('WTO QR returned HTTP ' + str(r.status_code))
            chunks = []
            size = 0
            for chunk in r.iter_content(65536):
                size += len(chunk)
                if size > 8 * 1024 * 1024:
                    raise RuntimeError('QR response exceeds 8 MiB; narrow filters')
                chunks.append(chunk)
        data = json.loads(b''.join(chunks))
    except requests.RequestException as e:
        raise RuntimeError('WTO QR network request failed: ' + type(e).__name__) from None
    if not isinstance(data, dict) or (endpoint == 'detail' and (not isinstance(data.get('data'), dict))) or (endpoint != 'detail' and (not isinstance(data.get('data'), list) or not isinstance(data.get('meta'), dict))):
        raise RuntimeError('Unexpected WTO QR response')
    return {'source': 'WTO Quantitative Restrictions API', 'source_info': 'https://apiportal.wto.org/api-details#api=quantitative-restrictions', 'endpoint': endpoint, 'selection': params, 'response': data, 'note': '报告的非关税数量限制措施，产品代码按任意HS版本前缀匹配；是否仍生效以及法律依据、通知和后续修改须查原始官方来源。分页和总数以返回meta为准，不是法律意见。QR成员代码与时间序列代码可能不同。'}
