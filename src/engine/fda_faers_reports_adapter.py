"""openFDA FAERS drug event reports: reported associations, not causation."""
import release_runtime
import json, os, re
import requests
URL = 'https://api.fda.gov/drug/event.json'

def search(medicine, limit=2, skip=0):
    if not isinstance(medicine, str) or not re.fullmatch('[A-Za-z0-9][A-Za-z0-9 .-]{0,79}', medicine.strip()):
        raise ValueError('Use a medicine name of 1–80 letters, numbers, spaces, dots or hyphens')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, skip))) or not 1 <= limit <= 10 or (not 0 <= skip <= 25000):
        raise ValueError('Invalid pagination')
    params = {'search': 'patient.drug.medicinalproduct:"' + medicine.strip() + '"', 'limit': limit, 'skip': skip}
    key = release_runtime.environment.get('OPENFDA_API_KEY')
    if key:
        params['api_key'] = key
    try:
        with requests.get(URL, params=params, timeout=30, stream=True, allow_redirects=False) as r:
            if r.is_redirect:
                raise RuntimeError('Unexpected FDA redirect')
            status = r.status_code
            raw = bytearray()
            for chunk in r.iter_content(65536):
                raw.extend(chunk)
                if len(raw) > 8000000:
                    raise RuntimeError('FDA response exceeds 8 MB; reduce limit')
    except requests.RequestException as e:
        raise RuntimeError('FDA request failed: ' + type(e).__name__) from None
    data = json.loads(raw)
    if status == 404 and data.get('error', {}).get('code') == 'NOT_FOUND':
        return {'source': 'openFDA FAERS drug event API', 'source_info': 'https://open.fda.gov/apis/drug/event/', 'selection': {'medicine': medicine, 'limit': limit, 'skip': skip}, 'returned': 0, 'results': [], 'note': 'FDA 未返回匹配报告；不代表没有风险或未发生事件。'}
    if status != 200:
        raise RuntimeError('FDA API returned HTTP ' + str(status))
    if not isinstance(data, dict) or not isinstance(data.get('results'), list) or (not isinstance(data.get('meta'), dict)):
        raise RuntimeError('Unexpected FDA response')
    return {'source': 'openFDA FAERS drug event API', 'source_info': 'https://open.fda.gov/apis/drug/event/', 'selection': {'medicine': medicine, 'limit': limit, 'skip': skip}, 'returned': len(data['results']), 'response': data, 'note': '自发及其他不良事件报告可能重复、漏报、信息不完整、延迟且含合用药；匹配药物不证明其导致该事件，报告数不等于发生人数、风险或发生率，不能比较药品安全性。公开记录非个体诊疗建议。'}
