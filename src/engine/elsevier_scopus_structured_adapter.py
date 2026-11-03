"""Structured Scopus search using existing institution-authorized API adapter."""
import release_runtime
from elsevier_scopus_official_adapter import search as upstream

def search(keyword, field='topic', author_last='', start_year=None, end_year=None, start=0, count=5):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 300 or any((c in keyword for c in ['"', '\\', '\n', '\r'])):
        raise ValueError('invalid keyword')
    if field not in ('topic', 'title'):
        raise ValueError('field must be topic or title')
    if not isinstance(author_last, str) or len(author_last) > 100 or any((c in author_last for c in ['"', '\\', '\n', '\r'])):
        raise ValueError('invalid author surname')
    if (start_year is None) != (end_year is None) or (start_year is not None and (type(start_year) is not int or type(end_year) is not int or (not 1900 <= start_year <= end_year <= 2100))):
        raise ValueError('provide valid publication years together')
    q = ('TITLE-ABS-KEY' if field == 'topic' else 'TITLE') + '("' + keyword.strip() + '")'
    if author_last.strip():
        q += ' AND AUTHLASTNAME("' + author_last.strip() + '")'
    if start_year is not None:
        q += ' AND PUBYEAR AFT ' + str(start_year - 1) + ' AND PUBYEAR BEF ' + str(end_year + 1)
    x = upstream(q, start, count)
    x['structured_filters'] = {'keyword': keyword.strip(), 'field': field, 'author_last': author_last.strip() or None, 'publication_year_range': [start_year, end_year] if start_year is not None else None}
    x['note'] += ' 作者姓氏可能重名，年份为 Scopus 源检索口径；对应 DOI 可进一步查询官方详情，全文和学校订购状态不能由命中推断。'
    return x
