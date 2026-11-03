"""U.S. BLS public API v1 bounded multiple-series query."""
import release_runtime
import re, requests
from bls_public_adapter import KNOWN
URL = 'https://api.bls.gov/publicAPI/v1/timeseries/data/'

def query(series_ids, start, end):
    if not isinstance(series_ids, list) or not 1 <= len(series_ids) <= 25 or any((not isinstance(s, str) or not re.fullmatch('[A-Z0-9]{5,40}', s) for s in series_ids)) or (len(set(series_ids)) != len(series_ids)):
        raise ValueError('provide 1–25 distinct uppercase BLS series IDs')
    if any((type(y) is not int for y in (start, end))) or not 1900 <= start <= end <= 2100 or end - start > 9:
        raise ValueError('v1 supports at most 10 consecutive years')
    body = {'seriesid': series_ids, 'startyear': str(start), 'endyear': str(end)}
    with requests.post(URL, json=body, timeout=(10, 25), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        raw = bytearray()
        for part in r.iter_content(65536):
            raw.extend(part)
            if len(raw) > 8000000:
                raise ValueError('response exceeds 8 MB')
    j = __import__('json').loads(raw)
    if not isinstance(j, dict) or j.get('status') != 'REQUEST_SUCCEEDED':
        raise RuntimeError('BLS query not successful: ' + str(j.get('message', 'unknown'))[:300])
    rows = (j.get('Results') or {}).get('series')
    if not isinstance(rows, list):
        raise RuntimeError('unexpected BLS response')
    seen = set()
    for s in rows:
        id = s.get('seriesID') if isinstance(s, dict) else None
        if id not in series_ids or id in seen or (not isinstance(s.get('data'), list)):
            raise RuntimeError('unexpected or duplicate BLS series')
        seen.add(id)
        for v in s['data']:
            y = v.get('year') if isinstance(v, dict) else None
            if not isinstance(y, str) or not re.fullmatch('\\d{4}', y) or (not start <= int(y) <= end):
                raise RuntimeError('BLS response outside requested year range')
    return {'source_url': URL, 'request': body, 'series': rows, 'missing_series_ids': [i for i in series_ids if i not in seen], 'known_descriptions': {i: KNOWN[i] for i in series_ids if i in KNOWN}, 'source_messages': j.get('message', []), 'note': 'BLS 公共 v1 未提供通用系列名称和单位元数据；未列入 known_descriptions 的代码须查 BLS 官方目录。保留原始值、期间、脚注和缺失，空序列非零；不同系列单位不可混同。未注册版本每日25次、单次最多25系列及10年，配额以官方最新规则为准。'}
