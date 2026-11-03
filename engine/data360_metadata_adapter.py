"""World Bank Data360 official indicator metadata and disaggregation codes."""
import release_runtime
import json, re, requests
BASE = 'https://data360api.worldbank.org/data360/'

def _validate(dataset, indicator):
    if any((not isinstance(v, str) or not re.fullmatch('[A-Za-z0-9_.-]{1,100}', v) for v in (dataset, indicator))):
        raise ValueError('invalid dataset or indicator code')

def _read(method, url, **kwargs):
    with requests.request(method, url, timeout=(10, 25), stream=True, allow_redirects=False, **kwargs) as r:
        r.raise_for_status()
        body = bytearray()
        for part in r.iter_content(65536):
            body.extend(part)
            if len(body) > 5000000:
                raise ValueError('response exceeds 5 MB')
    return json.loads(body)

def metadata(dataset, indicator):
    _validate(dataset, indicator)
    payload = {'query': f"&$filter=series_description/idno eq '{indicator}' and series_description/database_id eq '{dataset}'"}
    j = _read('POST', BASE + 'metadata', json=payload)
    rows = j.get('value') if isinstance(j, dict) else None
    count = j.get('@odata.count') if isinstance(j, dict) else None
    if not isinstance(rows, list) or type(count) is not int or count != len(rows) or any((not isinstance(x, dict) or (x.get('series_description') or {}).get('idno') != indicator or (x.get('series_description') or {}).get('database_id') != dataset for x in rows)):
        raise RuntimeError('unexpected or mismatched metadata')
    return {'source_url': BASE + 'metadata', 'request': payload, 'count': count, 'items': rows, 'note': '原始官方指标元数据；无记录不等于数据为零，定义、单位和更新以来源为准。'}

def disaggregations(dataset, indicator):
    _validate(dataset, indicator)
    params = {'datasetId': dataset, 'indicatorId': indicator}
    j = _read('GET', BASE + 'disaggregation', params=params)
    if not isinstance(j, list) or any((not isinstance(x, dict) or not isinstance(x.get('field_name'), str) or (not isinstance(x.get('field_value'), list)) for x in j)):
        raise RuntimeError('unexpected disaggregation response')
    return {'source_url': BASE + 'disaggregation', 'request': params, 'dimensions': j, 'note': '各维度列出源接口可能代码，不表示任意地区、时间与代码组合均有观测。'}
