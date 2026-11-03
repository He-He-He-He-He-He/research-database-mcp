"""Scopus 主题与机构、国家和刊物字段的官方组合检索。"""
import release_runtime
import re
from elsevier_scopus_official_adapter import search as upstream

def search(keyword, field='topic', organization='', country='', journal='', affiliation_id='', author_last='', start_year=None, end_year=None, start=0, count=5):
    values = {'keyword': keyword, 'organization': organization, 'country': country, 'journal': journal, 'author_last': author_last}
    for name, value in values.items():
        if not isinstance(value, str) or len(value) > 300 or any((c in value for c in ('"', '\\', '\n', '\r'))) or any((ord(c) < 32 for c in value)):
            raise ValueError(name + ' 须为不含引号及控制字符的单行文本，最多 300 字')
    if not keyword.strip():
        raise ValueError('主题或标题不能为空')
    if field not in ('topic', 'title'):
        raise ValueError('field 须为 topic 或 title')
    if not isinstance(affiliation_id, str) or (affiliation_id and (not re.fullmatch('[1-9][0-9]{0,15}', affiliation_id))):
        raise ValueError('Scopus 机构 ID 须为正整数字符串')
    if (start_year is None) != (end_year is None) or (start_year is not None and (type(start_year) is not int or type(end_year) is not int or (not 1900 <= start_year <= end_year <= 2100))):
        raise ValueError('发表年份应提供合法起止年份')
    q = ('TITLE-ABS-KEY' if field == 'topic' else 'TITLE') + '("' + keyword.strip() + '")'
    for tag, name in [('AFFILORG', 'organization'), ('AFFILCOUNTRY', 'country'), ('SRCTITLE', 'journal'), ('AUTHLASTNAME', 'author_last')]:
        if values[name].strip():
            q += ' AND ' + tag + '("' + values[name].strip() + '")'
    if affiliation_id:
        q += ' AND AF-ID(' + affiliation_id + ')'
    if start_year is not None:
        q += ' AND PUBYEAR AFT ' + str(start_year - 1) + ' AND PUBYEAR BEF ' + str(end_year + 1)
    out = upstream(q, start, count)
    out['structured_filters'] = {**{k: v.strip() or None for k, v in values.items()}, 'field': field, 'affiliation_id': affiliation_id or None, 'publication_year_range': [start_year, end_year] if start_year is not None else None}
    out['field_documentation'] = 'https://service.elsevier.com/app/answers/detail/a_id/11365/supporthub/scopus/'
    out['note'] += ' 国家、机构及作者条件按文献记录匹配，不能推断所选作者与选定机构对应；SRCTITLE 不一定只匹配期刊。Scopus 机构 ID 与 SciVal 机构 ID 不可混用。原站动态排序可能变化，记录及全文权限需另核对。'
    return out
