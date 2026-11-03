"""DOAJ open journal/article metadata search and exact record lookup."""
import release_runtime
import re, requests
from urllib.parse import quote
BASE = 'https://doaj.org/api/v4/'

def _get(path, params=None):
    with requests.get(BASE + path, params=params, timeout=(10, 25), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        source = r.url
        buf = bytearray()
        for b in r.iter_content(65536):
            buf.extend(b)
            if len(buf) > 8000000:
                raise ValueError('DOAJ response exceeds 8 MB')
    import json
    try:
        j = json.loads(buf)
    except ValueError:
        raise RuntimeError('DOAJ returned non-JSON') from None
    if not isinstance(j, dict):
        raise RuntimeError('unexpected DOAJ response')
    return (source, j)

def search(keyword, entity='articles', field='all', year=None, issn='', page=1, size=10):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200 or any((x in keyword for x in ['"', '\\', '\n', '\r'])):
        raise ValueError('invalid keyword')
    if entity not in ('articles', 'journals') or field not in ('all', 'title', 'abstract'):
        raise ValueError('invalid entity or field')
    if entity == 'journals' and (year is not None or field == 'abstract'):
        raise ValueError('year and abstract filters are for article records')
    if year is not None and (type(year) is not int or not 1800 <= year <= 2100):
        raise ValueError('invalid publication year')
    if not isinstance(issn, str) or (issn and (not re.fullmatch('\\d{4}-\\d{3}[\\dXx]', issn))):
        raise ValueError('invalid ISSN')
    if type(page) is not int or not 1 <= page <= 100 or type(size) is not int or (not 1 <= size <= 25):
        raise ValueError('invalid page or size')
    prefix = {'all': '', 'title': 'title:', 'abstract': 'bibjson.abstract:'}[field]
    query = prefix + '"' + keyword.strip() + '"'
    if year is not None:
        query += ' AND bibjson.year:' + str(year)
    if issn:
        query += ' AND issn:' + issn.upper()
    u, j = _get('search/' + entity + '/' + quote(query, safe=''), {'page': page, 'pageSize': size})
    rows = j.get('results')
    if type(j.get('total')) is not int or not isinstance(rows, list) or len(rows) > size or any((not isinstance(x, dict) or not re.fullmatch('[a-f0-9]{32}', str(x.get('id', ''))) for x in rows)):
        raise RuntimeError('unexpected DOAJ search response')
    if year is not None and any((str((x.get('bibjson') or {}).get('year', '')) != str(year) for x in rows)):
        raise RuntimeError('DOAJ response includes unexpected publication year')
    return {'source_url': u, 'query': query, 'entity': entity, 'source_total': j.get('total'), 'page': page, 'page_size': size, 'items': rows, 'note': 'DOAJ 开放获取目录元数据，不代表每篇全文永久可取；期刊与文章收录范围不同。筛选按来源搜索语法，跨页和结果可能变化；具体授权、发表年份及全文链接以原记录为准。'}

def detail(entity, record_id):
    if entity not in ('articles', 'journals') or not isinstance(record_id, str) or (not re.fullmatch('[a-f0-9]{32}', record_id)):
        raise ValueError('invalid DOAJ entity or ID')
    u, j = _get(entity + '/' + record_id)
    if j.get('id') != record_id or not isinstance(j.get('bibjson'), dict):
        raise RuntimeError('DOAJ returned mismatched record')
    return {'source_url': u, 'entity': entity, 'record': j, 'note': 'DOAJ 原始期刊/文章元数据；对全文可用性、同行评审和许可应核对具体来源及版本。'}
