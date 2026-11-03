"""UN InforMEA treaty index and related meetings / decisions."""
import release_runtime
import json, re
import requests
BASE = 'https://odata.informea.org/informea.svc/'

def _get(entity, params):
    with requests.get(BASE + entity, params=params, timeout=30, stream=True, allow_redirects=False) as r:
        if r.is_redirect or not r.ok:
            raise RuntimeError('InforMEA returned HTTP ' + str(r.status_code))
        raw = bytearray()
        for part in r.iter_content(65536):
            raw.extend(part)
            if len(raw) > 8000000:
                raise RuntimeError('InforMEA response exceeds 8 MB')
    data = json.loads(raw)
    d = data.get('d', {})
    if not isinstance(d.get('results'), list):
        raise RuntimeError('Unexpected InforMEA response')
    return d

def treaties(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('Invalid keyword')
    d = _get('Treaties', {'$format': 'json', '$top': 500, '$inlinecount': 'allpages', '$orderby': 'id'})
    if '__count' not in d or not str(d['__count']).isdigit() or int(d['__count']) != len(d['results']):
        raise RuntimeError('InforMEA treaty list incomplete')
    matches = [x for x in d['results'] if keyword.casefold() in ' '.join((str(x.get(k) or '') for k in ('id', 'titleEnglish', 'officialNameEnglish'))).casefold()]
    return {'source': 'UN InforMEA OData treaty index', 'source_info': 'https://www.informea.org/en/about/informea-api-catalogue', 'source_url': BASE + 'Treaties', 'matched_total': len(matches), 'items': matches, 'note': '按标识及英文名称本地子串筛选；保留原字段，不代表条约对特定国家已生效。来源聚合，使用需核原协定及缔约方状态。InforMEA 条件为非商业用途并保留署名。'}

def records(entity, treaty, offset=0, limit=10):
    if entity not in ('meetings', 'decisions'):
        raise ValueError('Unsupported entity')
    if not isinstance(treaty, str) or not re.fullmatch('[A-Za-z0-9_-]{1,80}', treaty):
        raise ValueError('Use treaty ID from treaty index')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (offset, limit))) or offset < 0 or (not 1 <= limit <= 100):
        raise ValueError('Invalid pagination')
    name = entity.title()
    p = {'$format': 'json', '$top': limit, '$skip': offset, '$inlinecount': 'allpages', '$orderby': 'id', '$filter': "treaty eq '" + treaty + "'"}
    d = _get(name, p)
    if any((x.get('treaty') != treaty for x in d['results'])):
        raise RuntimeError('InforMEA filter not honored')
    return {'source': 'UN InforMEA OData ' + entity, 'source_info': 'https://www.informea.org/en/about/informea-api-catalogue', 'source_url': BASE + name, 'selection': {'treaty': treaty, 'offset': offset, 'limit': limit}, 'response': d, 'note': '保留原始字段及 OData 时间；这是所选条约的索引记录，决议状态不必然意味着对特定国家的法律效力。分页总数和内容可能变动；来源聚合，核原文及生效状态。InforMEA 条件为非商业用途并保留署名。'}
