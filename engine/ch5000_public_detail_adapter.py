"""Public trial epigraphic metadata detail; the upstream uses plain HTTP."""
import release_runtime
import re
import requests
BASE = 'http://121.89.86.151:8000/api/v1/data/infos/'
FIELDS = ('id', 'name', 'alias', 'dynasty', 'era_name', 'common_era', 'language', 'inscription', 'main_inscription', 'material', 'form', 'shape', 'composition', 'author', 'inscriber', 'font', 'excavation_site', 'collector', 'source')

def detail(info_id, timeout=25):
    if not isinstance(info_id, str) or not re.fullmatch('enc_[A-Za-z0-9_-]{20,100}', info_id):
        raise ValueError('invalid info_id')
    try:
        response = requests.get(BASE + info_id + '/', timeout=timeout)
        response.raise_for_status()
        body = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise RuntimeError('题录详情请求失败') from None
    row = body.get('datas') if isinstance(body, dict) and body.get('code') == 200 else None
    if not isinstance(row, dict) or row.get('id') != info_id or (not isinstance(row.get('name'), str)) or (not row['name'].strip()):
        raise RuntimeError('题录详情响应无效或标识不一致')
    safe = {}
    for key in FIELDS:
        value = row.get(key)
        if value is None or (isinstance(value, (str, int)) and (not isinstance(value, bool))):
            if isinstance(value, str) and (re.search('https?://|[?&](?:token|session|key)=', value, re.I) or len(value) > 10000):
                continue
            safe[key] = value
    return {'source': '中国金石总录试用库', 'record': safe, 'note': '使用检索结果的 info_id，区别于 id；上游 HTTP，勿发送敏感信息。机构身份、图像和全文权限未验证；馆方列试用至 2026-12-31。'}
