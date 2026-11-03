"""UNESCO UIS repeated-indicator and repeated-geography official data API."""
import release_runtime
import json, re, requests
URL = 'https://api.uis.unesco.org/api/public/data/indicators'

def query(indicators, geographies, start, end):
    if not isinstance(indicators, list) or not 1 <= len(indicators) <= 20 or any((not isinstance(v, str) or not re.fullmatch('[A-Za-z0-9_.-]{1,80}', v) for v in indicators)) or (len(set(indicators)) != len(indicators)):
        raise ValueError('provide 1–20 distinct indicator codes')
    if not isinstance(geographies, list) or not 1 <= len(geographies) <= 20 or any((not isinstance(v, str) or not re.fullmatch('[A-Z0-9_-]{2,20}', v) for v in geographies)) or (len(set(geographies)) != len(geographies)):
        raise ValueError('provide 1–20 distinct UIS geography codes')
    if any((type(x) is not int for x in (start, end))) or not 1900 <= start <= end <= 2100:
        raise ValueError('invalid year range')
    params = [('indicator', x) for x in indicators] + [('geoUnit', x) for x in geographies] + [('start', start), ('end', end), ('footnotes', 'true'), ('indicatorMetadata', 'true')]
    with requests.get(URL, params=params, timeout=(10, 30), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        url = r.url
        body = bytearray()
        for part in r.iter_content(65536):
            body.extend(part)
            if len(body) > 10000000:
                raise ValueError('response exceeds 10 MB; narrow selection')
    j = json.loads(body)
    rows = j.get('records') if isinstance(j, dict) else None
    meta = j.get('indicatorMetadata') if isinstance(j, dict) else None
    if not isinstance(rows, list) or not isinstance(meta, list):
        raise RuntimeError('unexpected UNESCO response')
    if any((not isinstance(x, dict) or x.get('indicatorId') not in indicators or x.get('geoUnit') not in geographies or (type(x.get('year')) is not int) or (not start <= x['year'] <= end) for x in rows)):
        raise RuntimeError('response outside requested indicators, geographies or years')
    if any((not isinstance(x, dict) or x.get('indicatorCode') not in indicators for x in meta)):
        raise RuntimeError('metadata outside requested indicators')
    return {'source_url': url, 'count': len(rows), 'records': rows, 'indicator_metadata': meta, 'hints': j.get('hints', []), 'note': '保留原始值、magnitude、限定符与逐条脚注；指标元数据的单位与口径可能不同。空记录不等于零；来源单次最多100000条，本工具响应上限10MB，超限请缩小范围。'}
