"""Structured queries and exact DOI resolution using Clarivate WOS Starter API."""
import release_runtime
import re
from clarivate_wos_starter_adapter import search as upstream_search
from clarivate_wos_starter_detail_adapter import detail as upstream_detail

def search(keyword, field='topic', author='', start=None, end=None, page=1, limit=5, sort_field=''):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 300 or any((c in keyword for c in ['"', '\\', '\n', '\r'])):
        raise ValueError('invalid keyword')
    if field not in ('topic', 'title'):
        raise ValueError('field must be topic or title')
    if not isinstance(author, str) or len(author) > 100 or any((c in author for c in ['"', '\\', '\n', '\r'])):
        raise ValueError('invalid author')
    if (start is None) != (end is None) or (start is not None and (type(start) is not int or type(end) is not int or (not 1900 <= start <= end <= 2100))):
        raise ValueError('provide valid publication years together')
    query = ('TS' if field == 'topic' else 'TI') + '=("' + keyword.strip() + '")'
    if author.strip():
        query += ' AND AU=("' + author.strip() + '")'
    if start is not None:
        query += ' AND PY=(' + str(start) + '-' + str(end) + ')'
    result = upstream_search(query, 'WOS', page, limit, sort_field=sort_field)
    result['structured_filters'] = {'keyword': keyword.strip(), 'field': field, 'author': author.strip() or None, 'publication_year_range': [start, end] if start is not None else None}
    result['note'] += ' PY 按 Web of Science 来源口径可能匹配早期在线或最终发表年份；作者姓名可能重名，详情需核实。'
    return result

def doi_detail(doi):
    if not isinstance(doi, str) or not re.fullmatch('10\\.\\d{4,9}/[^\\s"\\\\]{1,450}', doi, re.I):
        raise ValueError('invalid DOI')
    result = upstream_search('DO=("' + doi + '")', 'WOS', 1, 10)
    matches = [x for x in result['items'] if str((x.get('identifiers') or {}).get('doi', '')).casefold() == doi.casefold()]
    if len(matches) != 1:
        return {'doi': doi, 'matched_on_page': len(matches), 'candidates': [{'uid': x.get('uid'), 'title': x.get('title')} for x in matches], 'note': '未找到唯一精确 DOI；仅检查前10条，不能判定库中不存在，也不自动选择。'}
    uid = matches[0].get('uid')
    x = upstream_detail(uid)
    x['requested_doi'] = doi
    x['search_metadata'] = result['metadata']
    return x
