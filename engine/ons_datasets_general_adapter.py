"""UK ONS open dataset catalogue, dimensions and observations.

Different datasets have different geographies, versions, units and methods.
Census 2021 covers England and Wales, not all of the UK. Official API is beta.
"""
import release_runtime
import re
import requests
from diagnostics import SourceError
BASE = 'https://api.beta.ons.gov.uk/v1/'

def _part(value):
    if not isinstance(value, str) or not re.fullmatch('[A-Za-z0-9_-]{1,120}', value):
        raise ValueError('invalid ONS path component')
    return value

def _get(path, params=None):
    from diagnostics import request_error, SourceError
    try:
        r = requests.get(BASE + path, params=params, timeout=30)
        r.raise_for_status()
    except requests.RequestException as exc:raise request_error(exc,BASE+path) from None
    try:return r.json()
    except ValueError:raise SourceError('invalid_json_response','ONS 返回非 JSON',url=BASE+path,transport='requests') from None

def catalogue(limit=20, offset=0):
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or offset < 0:
        raise ValueError('limit must be 1..100 and offset nonnegative')
    return _get('datasets', {'limit': limit, 'offset': offset})

def discover(keyword, offset=0, max_pages=4, limit=30):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100:
        raise ValueError('invalid keyword')
    if type(offset) is not int or offset < 0 or type(max_pages) is not int or (not 1 <= max_pages <= 10) or (type(limit) is not int) or (not 1 <= limit <= 100):
        raise ValueError('invalid search bounds')
    q = keyword.strip().casefold()
    cursor = offset
    scanned = 0
    matches = []
    totals = []
    errors = []
    pages = 0
    while pages < max_pages:
        try:
            batch = catalogue(100, cursor)
        except (SourceError, ValueError) as exc:
            errors.append({'offset':cursor,'error':str(exc),'diagnostics':exc.as_dict() if isinstance(exc,SourceError) else {'kind':'invalid_response'}})
            break
        if not isinstance(batch, dict) or not isinstance(batch.get('items'), list) or type(batch.get('total_count')) is not int:
            errors.append({'offset': cursor, 'error': 'invalid response'})
            break
        rows = batch['items']
        total = batch['total_count']
        totals.append(total)
        pages += 1
        for x in rows:
            if isinstance(x, dict) and any((q in str(x.get(k, '')).casefold() for k in ('id', 'title', 'description'))):
                matches.append(x)
        scanned += len(rows)
        cursor += len(rows)
        if not rows or cursor >= total:
            break
    if errors and pages==0:
        info=errors[0].get('diagnostics',{'kind':'invalid_response'})
        raise SourceError(info.get('kind','invalid_response'),errors[0]['error'],url=BASE+'datasets',status=info.get('http_status'),transport=info.get('transport'))
    complete = bool(totals) and (not errors) and (len(set(totals)) == 1) and (cursor >= totals[-1]) and (offset == 0)
    return {'source': 'UK Office for National Statistics', 'keyword': keyword.strip(), 'start_offset': offset, 'scanned': scanned, 'pages': pages, 'observed_totals': totals, 'matching_scanned': len(matches), 'items': matches[:limit], 'matches_truncated': len(matches) > limit, 'next_offset': cursor if errors or not totals or cursor < totals[-1] else None, 'failed_pages': errors, 'complete_from_start': complete, 'note': '仅在已扫描的数据集 ID、标题与描述中本地匹配；目录与排序可能更新，未扫描或失败页不代表无匹配。'}

def _version(dataset, edition, version):
    return f'datasets/{_part(dataset)}/editions/{_part(edition)}/versions/{_part(str(version))}'

def editions(dataset):
    return _get('datasets/' + _part(dataset) + '/editions')

def dimensions(dataset, edition, version):
    return _get(_version(dataset, edition, version) + '/dimensions')

def options(dataset, edition, version, dimension, limit=100, offset=0):
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or offset < 0:
        raise ValueError('limit must be 1..100 and offset nonnegative')
    return _get(_version(dataset, edition, version) + '/dimensions/' + _part(dimension) + '/options', {'limit': limit, 'offset': offset})

def metadata(dataset, edition, version):
    return _get(_version(dataset, edition, version) + '/metadata')

def observations(dataset, edition, version, dimensions):
    """CMD observation endpoint: each dimension requires one option; one may be wildcard."""
    if not isinstance(dimensions, dict) or not dimensions:
        raise ValueError('dimensions must be a nonempty mapping')
    for key, val in dimensions.items():
        _part(key)
        if not isinstance(val, str) or not val or len(val) > 120:
            raise ValueError('invalid option')
    return _get(_version(dataset, edition, version) + '/observations', dimensions)

def census(dataset, edition, version, area_type):
    """Census 2021 json endpoint, with area-type e.g. ctry,W92000004."""
    if not isinstance(area_type, str) or not re.fullmatch('[A-Za-z0-9_-]+,[A-Za-z0-9_-]+', area_type):
        raise ValueError('area_type must be type,code')
    return _get(_version(dataset, edition, version) + '/json', {'area-type': area_type})
